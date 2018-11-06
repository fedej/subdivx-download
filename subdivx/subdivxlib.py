import argparse
import logging
import logging.handlers
import os
import urllib.parse
import urllib.request

from difflib import SequenceMatcher
from tempfile import NamedTemporaryFile
from zipfile import is_zipfile, ZipFile

from bs4 import BeautifulSoup

RAR_ID = bytes("Rar!\x1a\x07\x00","utf-8")

SUBDIVX_SEARCH_URL = "http://www.subdivx.com/index.php?buscar=%s+%s&accion=5&masdesc=&subtitulos=1&realiza_b=1&oxdown=1"
SUBDIVX_DOWNLOAD_MATCHER = {'name':'a', 'rel':"nofollow", 'target': "new"}

LOGGER_LEVEL = logging.DEBUG
LOGGER_FORMATTER = logging.Formatter('%(asctime)-25s %(levelname)-8s %(name)-29s %(message)s', '%Y-%m-%d %H:%M:%S')

class NoResultsError(Exception):
    pass


def is_rarfile(fn):
    '''Check quickly whether file is rar archive.'''
    buf = open(fn, "rb").read(len(RAR_ID))
    return buf == RAR_ID


def setup_logger(level, log_file):
    global logger
    logger = logging.getLogger()
    logfile = logging.handlers.RotatingFileHandler(log_file, maxBytes=1000 * 1024, backupCount=9)
    logfile.setFormatter(LOGGER_FORMATTER)
    logger.addHandler(logfile)
    logger.setLevel(level)
    return logger


def get_subtitle_url(series_name, series_id, series_quality, skip=0):
    enc_series_name = urllib.parse.quote(series_name)
    enc_series_id = urllib.parse.quote(series_id)

    logger.debug('Starting request to subdivx.com')
    page = urllib.request.urlopen(SUBDIVX_SEARCH_URL % (enc_series_name, enc_series_id))
    logger.debug('Search Query URL: ' + page.geturl())

    soup = BeautifulSoup(page, features="html.parser")

    results_descriptions = soup('div', id='buscador_detalle_sub')

    if not results_descriptions:
        raise(NoResultsError(' '.join(['No suitable subtitles were found for:',
                                      series_name,
                                      series_id,
                                      series_quality])))

    search_match = '%s %s %s' % (series_name, series_id, series_quality)
    matcher = SequenceMatcher(lambda x: x==" " or x==".", search_match)

    def calculate_ratio(seq):
        matcher.set_seq2(seq)

        blocks = matcher.get_matching_blocks()

        scores = []
        for block in blocks:
            long_start   = block[1] - block[0]
            long_end     = long_start + len(search_match)
            long_substr  = seq[long_start:long_end]

            m2 = SequenceMatcher(None, search_match, long_substr)
            r = m2.ratio()
            if r > .999:
                return 100
            else:
                scores.append(r)
        result = int(100 * sorted(scores, reverse=True)[skip:][0])
        return result

    best_match = [calculate_ratio(''.join([e for e in description.recursiveChildGenerator() if isinstance(e,str)]))
                  for description in results_descriptions]

    best_match_index = best_match.index(max(best_match))

    return results_descriptions[best_match_index].nextSibling.find(**SUBDIVX_DOWNLOAD_MATCHER)['href']

def get_subtitle(url, path, video_path):
    in_data = urllib.request.urlopen(url)
    temp_file = NamedTemporaryFile()

    temp_file.write(in_data.read())
    in_data.close()
    temp_file.seek(0)

    dest_path = os.path.dirname(os.path.abspath(video_path))
    if is_zipfile(temp_file.name):
        zip_file = ZipFile(temp_file)
        for name in zip_file.namelist():
            # don't unzip stub __MACOSX folders
            if '.srt' in name and '__MACOSX' not in name:
                logger.info(' '.join(['Unpacking zipped subtitle', name, 'to', dest_path]))
                zip_file.extract(name, dest_path)

        zip_file.close()

    elif is_rarfile(temp_file.name):
        rar_path = path + '.rar'
        logger.info('Saving rared subtitle as %s' % rar_path)
        with open(rar_path, 'wb') as out_file:
            out_file.write(temp_file.read())

        try:
            import subprocess
            #extract all .srt in the rared file
            ret_code = subprocess.call(['unrar', 'e', '-n*srt', rar_path, dest_path])
            if ret_code == 0:
                logger.info('Unpacking rared subtitle to %s' % dest_path)
                os.remove(rar_path)
        except OSError:
            logger.info('Unpacking rared subtitle failed.'
                        'Please, install unrar to automate this step.')
    temp_file.close()
