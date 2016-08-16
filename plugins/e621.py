# The MIT License (MIT)

# Copyright (c) 2015 kupiakos

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
import re
import html
from urllib.parse import urlsplit
import traceback

import json
import requests
import mimeparse
import praw


class e621Plugin:
    """
    Mirrors e621 images.
    Created by /u/HeyItsShuga

    """

    def __init__(self, useragent: str, **options):
        """Initialize the e621 importer.

        :param useragent: The useragent to use for querying e621.
        :param options: Other options in the configuration. Ignored.
        """
        self.log = logging.getLogger('lapis.e621')
        self.headers = {'User-Agent': useragent}
        self.regex = re.compile(r'^https?://(((?:www\.)?(?:static1\.)?((e621)|(e926))\.net/(data/.+/(?P<cdn_id>\w+))?(post/show/(?P<id>\d+)/?)?.*))$')

    def import_submission(self, submission: praw.objects.Submission) -> dict:
        """Import a submission from e621.

        This function will define the following values in its return data:
        - author: simply "an anonymous user on e621"
        - source: The url of the submission
        - importer_display/header
        - import_urls

        After we define that, we need to get the image. Since e621 has an API,
        we use that to try to get the image if the image is a non-CDN URL. If it is
        a CDN, we take the image directory and upload *that* to Imgur.

        image_url is the variable of the image to upload.

        :param submission: A reddit submission to parse.
        """
        print('e621 PLUGIN DEBUG - Initiated plugin.')
        try:
            url = html.unescape(submission.url)
            match = self.regex.match(submission.url)
            if not match:
                print('e621 PLUGIN DEBUG - Regex failed') ####################
                return None
            print('e621 PLUGIN DEBUG - Regex suceeded') ####################
            r = requests.head(url, headers=self.headers)
            mime_text = r.headers.get('Content-Type')
            mime = mimeparse.parse_mime_type(mime_text)
            if mime[0] == 'image':
                self.log.debug('Is CDN, no API needed')
                data = {'author': 'a e926 user',
                        'source': url,
                        'importer_display':
                            {'header': 'Mirrored e926 image:\n\n'}}
                image_url = url
            else:
                self.log.debug('Not CDN, will use API')
                match = self.regex.match(submission.url)
                match_data = match.groupdict()
                id = match_data.get('id') # Get ID out of regex.
                urlJ = 'http://e926.net/post/show.json?id=' + id
                self.log.debug('Will use API endpoint at ' + urlJ)
                callapi = requests.get(urlJ) # These next lines uses the API...
                json = callapi.json() # ...endpoint and gets the direct image URL to upload.
                img = (json['file_url'])
                uploader = (json['author'])
                data = {'author': 'an e926 user',
                        'source': url,
                        'importer_display':
                            {'header': 'LIVEMirrored e926 image by ' + uploader + ':\n\n'}}
                image_url = img # image_url is the image being mirrored.
            data['import_urls'] = [image_url]
            return data
        except Exception:
            self.log.error('Could not import e621 URL %s (%s)',
                           submission.url, traceback.format_exc())
            return None


__plugin__ = e621Plugin

# END OF LINE.
