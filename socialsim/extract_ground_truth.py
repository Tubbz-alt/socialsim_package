import pandas as pd

import pprint
import re
import json
import itertools
# import networkx as nx
import numpy as np
import glob
import ast
import networkx as nx

from datetime import datetime

from .twitter_cascade_reconstruction import full_reconstruction, get_reply_cascade_root_tweet

URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""


def get_urls(x):
    """
    Get list of URLS present in string passed
    :param x: string of text to extract URLs from
    :return:
    """
    urls = re.findall(URL_REGEX, x)
    # remove false positives
    urls = [x for x in urls if '/' in x and ',,' not in x]
    # remove any possible empty strings
    urls = [x for x in urls if x != '']
    return urls


def get_twitter_api_url_rep(x, name_suffix):
    if 'unwound' in x.keys():
        if x['unwound']['url' + name_suffix] != "":
            url = x['unwound']['url' + name_suffix]
        else:
            if 'expanded_url' + name_suffix in x.keys():
                url = x['expanded_url' + name_suffix]
            else:
                return ""
    elif 'expanded_url' + name_suffix in x.keys():
        url = x['expanded_url' + name_suffix]
    else:
        return ''
    return url


def get_twitter_urls(df, name_suffix):
    twitter_urls = []
    df_json = df.to_dict('records')
    for j_json in df_json:
        row_urls = []
        if "retweeted_status" in j_json.keys():
            try:
                api_urls = [get_twitter_api_url_rep(x, name_suffix) for x in
                            j_json["retweeted_status"]['entities']['urls'] if x != '']
            except:
                api_urls = []
            try:
                media_urls = [get_twitter_api_url_rep(x, name_suffix) for x in
                              j_json["retweeted_status"]['entities']['media'] if x != '']
            except:
                media_urls = []
            row_urls.extend(list(set(api_urls + media_urls)))
            # twitter_urls.append(urls)
        if "extension" in j_json.keys():
            try:
                api_urls = [get_twitter_api_url_rep(x, name_suffix) for x in j_json["extension"]['entities']['urls'] if
                            x != '']
                if 'resolved_urls' in j_json['extension'].keys():
                    resolved_urls = j_json['extension']['resolved_urls']
                    internal_urls = [x for x in api_urls if 'twitter.com' in x]
                    urls = list(set(resolved_urls + internal_urls))
                elif 'socialsim_resolved_urls' in j_json['extension'].keys():
                    resolved_urls = j_json['extension']['socialsim_resolved_urls']
                    internal_urls = [x for x in api_urls if 'twitter.com' in x]
                    urls = list(set(resolved_urls + internal_urls))
                else:
                    urls = api_urls
            except:
                urls = []
            row_urls.extend(urls)
            # twitter_urls.append(urls)
        if "entities" in j_json.keys():
            try:
                if len(j_json['entities']['urls']) > 0:
                    api_urls = [get_twitter_api_url_rep(x, name_suffix) for x in j_json['entities']['urls'] if x != '']
                    api_urls = [u for u in api_urls if not pd.isnull(u)]
                else:
                    if "media" in j_json["entities"].keys():
                        api_urls = [get_twitter_api_url_rep(x, name_suffix) for x in j_json["entities"]["media"] if
                                    x != '']
                    else:
                        api_urls = []
            except:
                if "media" in j_json["entities"].keys():
                    api_urls = [get_twitter_api_url_rep(x, name_suffix) for x in j_json["entities"]["media"] if x != '']
                else:
                    api_urls = []
            row_urls.extend(api_urls)
            # twitter_urls.append(api_urls)
        twitter_urls.append(list(set(row_urls)))
    return twitter_urls


def get_youtube_urls(df, text_suffix):
    youtube_urls = []
    for i, row in enumerate(df.iterrows()):
        rowdata = row[1]
        row_data_type = rowdata['kind']
        if 'resolved_urls' in rowdata['extension'].keys():
            urls = list(rowdata['extension']['resolved_urls'])
        elif 'socialsim_resolved_urls' in rowdata['extension'].keys():
            urls = list(rowdata['extension']['socialsim_resolved_urls'])
        else:
            if row_data_type == 'youtube#video':
                urls = get_urls(rowdata['snippet']['description' + text_suffix])
            elif row_data_type == 'youtube#commentThread':
                urls = get_urls(rowdata['snippet']['topLevelComment']['snippet']['textOriginal' + text_suffix])
            elif row_data_type == 'youtube#comment':
                urls = get_urls(rowdata['snippet']['textOriginal' + text_suffix])
            else:
                urls = []
        youtube_urls.append(urls)
    return youtube_urls


def get_domain(url):
    domains_shortened = {'redd.it': 'reddit.com', 'youtu.be': 'youtube.com',
                         'y2u.be': 'youtube.com', 't.co': 'twitter.com'}
    url = url.lower()
    if '://' in url:
        url = url.split('://')[1]
    domain = url.split('/')[0]
    if 'www.' in url:
        domain = domain.replace('www.', '')

    if domain in domains_shortened.keys():
        domain = domains_shortened[domain]
    return domain


def get_domains(urls):
    domains = []
    for url in urls:
        domain = get_domain(url)
        if domain not in domains:
            domains.append(domain)
    domains = list(set(domains))
    return domains


def get_youtube_text(row):
    row_data_type = row["kind"]
    if row_data_type == "youtube#caption":
        if not pd.isna(row["content"]):
            text = row["content"]["caption_m"]
        else:
            text = ""
    elif row_data_type == "youtube#channel" or row_data_type == "youtube#video":
        text = row["snippet"]["title_m"]
        text += row["snippet"]["description_m"]
    elif row_data_type == "youtube#comment":
        text = row["snippet"]["textOriginal_m"]
    elif row_data_type == "youtube#commentThread":
        text = row["snippet"]["topLevelComment"]["snippet"]["textOriginal_m"]
    else:
        text = ""
    return text


def has_link_external(domains, platform):
    for domain in domains:
        if f'{platform}.com' not in domain:
            return 1
    return 0


def parse_url(url):
    """
    Parse URL and resolve to base URL if includes a reference to a specific time in video, element on page,
    or if is a redirect, resolve to the link users would be redirected to on click.
    :param url: url (string)
    :return: url (string) after parsing (if applied, otherwise returns the original url string)
    """
    # consolidate youtube video URLs that may reference a specific time within the video etc. to the main video url
    if 'youtube.com/watch' in url:
        try:
            base, ext = url.split('?')
        except:
            return url
        split = ext.replace('&amp;', '&').split('&')
        ext = [x for x in split if x[:2] == 'v=']
        url = '?'.join([base] + ext)
    # consolidate youtube redirects to relect the URL being redirected to when clicking on link
    elif 'https://www.youtube.com/redirect?' in url:
        url = url.replace('&amp;', '&').split('&')
        # select the url in the redirect "q="
        try:
            url = [x for x in url if x[:2] == 'q='][0][2:]
        except IndexError:
            url = [x.split('q=', 1)[-1] for x in url if 'q=' in x][0]
        # format
        url = url.replace('%3A', ':').replace('%2F', '/')
    # consolidate references to users' page on youtube that may include query, e.g. whether to display videos in grid view
    # to simply url for user page with no query
    elif 'youtube.com/user/' in url:
        url = '/'.join([x for x in url.split('/') if '?' not in x])
    # consolidate urls that include a "referrer reference via "utm_source"
    elif '?utm_source' in url:
        url = url.split('?utm_source')[0]

    return url


def load_json(fn):
    json_data = []

    if type(fn) == str:
        with open(fn, 'rb') as f:
            for line in f:
                json_data.append(json.loads(line))
    else:
        for fn0 in fn:
            with open(fn0, 'rb') as f:
                for line in f:
                    json_data.append(json.loads(line))

    return (json_data)


def convert_timestamps(dataset, timestamp_field="nodeTime"):
    """
    Converts all timestamps to ISO 8601 formatted strings
    """

    try:
        dataset[timestamp_field] = pd.to_datetime(dataset[timestamp_field], unit='s')
    except:
        try:
            dataset[timestamp_field] = pd.to_datetime(dataset[timestamp_field], unit='ms')
        except:
            dataset[timestamp_field] = pd.to_datetime(dataset[timestamp_field])

    dataset[timestamp_field] = dataset[timestamp_field].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    return (dataset)


def get_info_id_from_text(text_list=[], keywords=[]):
    word_list = r"\b" + keywords[0] + r"\b"
    for w in keywords[1:]:
        word_list += "|" + r"\b" + w + r"\b"

    info_ids = []
    for text in text_list:
        info_ids += re.findall(word_list, text)

    return (list(set(info_ids)))


def get_info_id_from_fields(row, fields=['entities.hashtags.text'], casefold_info_ids=True):
    """
    Extract information IDs from specified fields in the JSON
    :param row: A DataFrame row containing the JSON fields
    :param fields: A list of field paths from which to extract the info IDs, e.g. entities.hashtags.text, entities.user_mentions.screen_name
    :returns: a list of information IDs that are in the specified fields
    """

    info_ids = []
    for path in fields:
        path = path.split('.')

        val = row.copy()

        for i, f in enumerate(path):

            if (isinstance(val, pd.Series) or type(val) == dict) and f in val.keys():
                # move down JSON path
                val = val[f]

            if type(val) == list:
                # iterate over list
                for v in val:
                    if type(v) == dict:
                        v = v[path[i + 1]]
                    info_ids.append(v)
                break
            elif i == len(path) and type(val) == str:
                info_ids.append(val)

    if casefold_info_ids:
        info_ids = [x.lower() for x in info_ids]

    return list(set(info_ids))


def user_alignment(alignment_file_path,
                   thresh=0.9):
    """
    Standardize user IDs across platforms based on released user alignment data.
    """

    alignment_files = glob.glob(alignment_file_path + '/Tng_an_userAlignment_*.json')

    alignment_data = []
    for fn in alignment_files:
        with open(fn, 'r') as f:
            for line in f:
                alignment_data.append(json.loads(line))

    df = pd.DataFrame(alignment_data)
    df = df[df['score'] > thresh]

    platforms = [c for c in df.columns if c != 'score']

    dfs = []
    for i, p1 in enumerate(platforms):
        for j, p2 in enumerate(platforms[i:]):
            if p2 != p1:
                df_map = df[[p1, p2, 'score']].dropna()
                df_map.columns = ['username1', 'username2', 'score']

                # if username has multiple matches keep the highest score
                df_map = df_map.sort_values('score', ascending=False)
                df_map = df_map.drop_duplicates(subset=['username2'])
                df_map = df_map.drop_duplicates(subset=['username1'])

                df_map = df_map.drop('score', axis=1)
                df_map = df_map[df_map['username1'] != df_map['username2']]

                dfs.append(df_map)

    edge_df = pd.concat(dfs, axis=0)
    edge_df = edge_df.drop_duplicates()

    G = nx.from_pandas_edgelist(edge_df, source='username1', target='username2')

    components = nx.connected_components(G)
    username_map = {}
    for comp in components:
        comp = list(comp)
        for i in range(len(comp) - 1):
            username_map[comp[i + 1]] = comp[0]

    return (username_map)


def extract_youtube_data(fn='youtube_data.json',
                         info_id_fields=None,
                         keywords=[],
                         anonymized=False,
                         username_map={},
                         additional_fields=[],
                         propagate_info_ids=False):
    platform = 'youtube'
    json_data = load_json(fn)
    data = pd.DataFrame(json_data)
    get_info_ids = False
    if not info_id_fields is None or len(keywords) > 0:
        get_info_ids = True

    if anonymized:
        name_suffix = "_h"
        text_suffix = "_m"
    else:
        name_suffix = ""
        text_suffix = ""

    output_columns = ['nodeID', 'nodeUserID', 'parentID', 'rootID', 'actionType', 'nodeTime', 'platform',
                      'has_URL', 'domain_linked', 'links_to_external', 'urls_linked'] + additional_fields
    if get_info_ids:
        output_columns.append('informationIDs')

    print('Deduplicating...')
    if '_id' in data.columns:
        del data['_id']
    data['row_str'] = ['&'.join(cols) for cols in data.astype(str).values]
    data = data.drop_duplicates(subset=['row_str']).reset_index(drop=True).copy()

    print('Extracting fields...')
    # extract URLS then add: has_URL, links_to_external, domain_linked
    urls_in_text = get_youtube_urls(data, text_suffix)
    data.loc[:, 'urls_linked'] = [[parse_url(y) for y in x] for x in urls_in_text]
    data.loc[:, 'has_URL'] = [int(len(x) > 0) for x in data['urls_linked']]
    data.loc[:, 'domain_linked'] = [get_domains(x) for x in data['urls_linked']]
    data.loc[:, 'links_to_external'] = [has_link_external(domains, platform) for domains in data['domain_linked']]

    # Get extra data
    data.loc[:, 'text'] = data.apply(get_youtube_text, axis=1)
    if "entities" not in data.keys():
        data["entities"] = None

    # Video + Caption merge and extraction
    # info_id_fields of caption (right table: y)
    def cap_info_id_fields(fields):
        cap_fields = []
        for path in fields:
            path = path.split('.')
            path = '.'.join([path[0] + '_y'] + path[1:])
            cap_fields.append(path)
        return cap_fields

    def get_vid_keywords(row, info_id_fields, vidCaps):
        keywords = get_info_id_from_fields(row, fields=info_id_fields)
        for idx, vidCap in vidCaps.loc[vidCaps['nodeID'] == row['nodeID']].iterrows():
            keywords += get_info_id_from_fields(vidCap, fields=cap_info_id_fields(info_id_fields))

        keywords = list(set(keywords))
        return keywords

    def safe_lambda(row, lam):
        """Try to extract the path from the row but catch any KeyErrors"""
        try:
            return lam(row)
        except KeyError:
            return None

    to_concat = []
    # extraction from 'youtube#video' and 'youtube#caption'
    videos = data[data['kind'] == 'youtube#video'].copy()
    videos.rename(columns={'id' + name_suffix: 'nodeID'}, inplace=True)
    captions = data[data['kind'] == 'youtube#caption']
    videos.loc[:, 'nodeTime'] = videos['snippet'].apply(lambda x: x['publishedAt'])
    videos.loc[:, 'parentID'] = videos['nodeID']
    videos.loc[:, 'rootID'] = videos['nodeID']
    videos.loc[:, 'actionType'] = 'video'
    videos.loc[:, 'platform'] = platform
    videos.loc[:, 'nodeUserID'] = videos['snippet'].apply(lambda x: x['channelId' + name_suffix])

    captions.loc[:, 'nodeID'] = captions['snippet'].apply(lambda x: x['videoId' + name_suffix])

    vidCaps = pd.merge(videos, captions, on='nodeID', how='inner')
    if len(keywords) > 0:
        raise NotImplementedError("It is not implemented for the merged text fields of video + caption")
    elif not info_id_fields is None:
        videos.loc[:, 'informationIDs'] = pd.Series(index=videos.index,
                                                    data=[get_vid_keywords(c, info_id_fields, vidCaps)
                                                          for i, c in videos.iterrows()])

    to_concat.append(videos)

    # Top-level comment extraction 
    comments = data[data['kind'] == 'youtube#commentThread'].copy()
    comments.loc[:, 'nodeTime'] = comments['snippet'].apply(lambda x: x['topLevelComment']['snippet']['publishedAt'])
    comments.loc[:, 'nodeID'] = comments['snippet'].apply(lambda x: x['topLevelComment']['id' + name_suffix])

    commentThread_author_f = lambda x: x['topLevelComment']['snippet']['authorChannelId']['value' + name_suffix]
    comments.loc[:, 'nodeUserID'] = comments['snippet'].apply(safe_lambda, args=(commentThread_author_f,))

    comVidIds = comments['snippet'].apply(lambda x: x['videoId' + name_suffix])
    comments.loc[:, 'parentID'] = comVidIds
    comments.loc[:, 'rootID'] = comVidIds
    comments.loc[:, 'actionType'] = 'comment'
    comments.loc[:, 'platform'] = platform
    if len(keywords) > 0:
        comments.loc[:, 'informationIDs'] = comments['snippet'].apply(
            lambda x: get_info_id_from_text([x['topLevelComment']['snippet']['textDisplay' + text_suffix]], keywords))
    elif not info_id_fields is None:
        comments.loc[:, 'informationIDs'] = pd.Series(index=comments.index,
                                                      data=[get_info_id_from_fields(r, info_id_fields) for i, r in
                                                            comments.iterrows()])

    to_concat.append(comments)

    # Reply extraction
    replies = data[data['kind'] == 'youtube#comment'].copy()
    replies.loc[:, 'nodeTime'] = replies['snippet'].apply(lambda x: x['publishedAt'])
    replies.rename(columns={'id' + name_suffix: 'nodeID'}, inplace=True)

    comment_author_f = lambda x: x['authorChannelId']['value' + name_suffix]
    replies.loc[:, 'nodeUserID'] = replies['snippet'].apply(safe_lambda, args=(comment_author_f,))

    replies.loc[:, 'parentID'] = replies['snippet'].apply(lambda x: x['parentId' + name_suffix])
    replies.loc[:, 'rootID'] = replies['snippet'].apply(lambda x: x['videoId' + name_suffix])
    replies.loc[:, 'actionType'] = 'comment'
    replies.loc[:, 'platform'] = platform
    if len(keywords) > 0:
        replies.loc[:, 'informationIDs'] = replies['snippet'].apply(
            lambda x: get_info_id_from_text([x['textDisplay' + text_suffix]], keywords))
    elif not info_id_fields is None:
        replies.loc[:, 'informationIDs'] = pd.Series(index=replies.index,
                                                     data=[get_info_id_from_fields(r, info_id_fields) for i, r in
                                                           replies.iterrows()])

    to_concat.append(replies)

    youtube_data = pd.concat(to_concat, ignore_index=True, sort=False)
    youtube_data = youtube_data[output_columns]

    print('Sorting...')
    youtube_data = youtube_data.sort_values("nodeTime").reset_index(drop=True)
    youtube_data = youtube_data.reset_index(drop=True)
    youtube_data['threadInfoIDs'] = pd.Series(index=youtube_data.index, data=[[] for i in range(len(youtube_data))])

    if propagate_info_ids and get_info_ids:
        youtube_data["propagated_informationIDs"] = youtube_data["informationIDs"]
        print('Adding information IDs to children...')
        # propagate infromation IDs to children
        finished = False
        count = 0
        while not finished:
            orig_info_ids = youtube_data['propagated_informationIDs'].copy()
            merged = youtube_data.reset_index().merge(youtube_data[['nodeID', 'propagated_informationIDs']], left_on='parentID',
                                                      right_on='nodeID',
                                                      suffixes=('', '_parent')).drop('nodeID_parent', axis=1).set_index(
                "index")

            merged['propagated_informationIDs'] = (merged['propagated_informationIDs'] + merged['propagated_informationIDs_parent']).apply(
                lambda x: sorted(list(set(x))))

            youtube_data.loc[merged.index, 'propagated_informationIDs'] = merged['propagated_informationIDs']
            finished = (merged['propagated_informationIDs'] == orig_info_ids.loc[merged.index]).all()
            count += 1
            print('Iteration ', count, (merged['propagated_informationIDs'] != orig_info_ids.loc[merged.index]).sum(),
                  ' nodes to update')
    
    if get_info_ids:
        # remove items without informationIDs
        youtube_data = youtube_data[youtube_data['informationIDs'].str.len() > 0]

        print('Expanding events...')
        # expand lists of info IDs into seperate rows
        # (i.e. an individual event is duplicated if it pertains to multiple information IDs)
        s = youtube_data.apply(lambda x: pd.Series(x['informationIDs']), axis=1).stack().reset_index(level=1, drop=True)
        s.name = 'informationID'
        youtube_data = youtube_data.drop(['informationIDs'], axis=1).join(s).reset_index(drop=True)

    youtube_data = youtube_data.drop('threadInfoIDs', axis=1)
    youtube_data = convert_timestamps(youtube_data)

    youtube_data['nodeUserID'] = youtube_data['nodeUserID'].replace(username_map)
    if get_info_ids:
        youtube_data = youtube_data[youtube_data['informationID'] != ''].copy()

    print('Done!')
    return youtube_data


def extract_telegram_data(fn='telegram_data.json',
                          info_id_fields=None,
                          keywords=[],
                          anonymized=False,
                          username_map={}):
    """
    Extracts fields from Telegram JSON data
    :param fn: A filename or list of filenames which contain the JSON Telegram data
    :param info_id_fields: A list of field paths from which to extract the information IDs. If None, don't extract any.
    """

    platform = 'telegram'
    json_data = load_json(fn)
    data = pd.DataFrame(json_data)

    get_info_ids = False
    if not info_id_fields is None or len(keywords) > 0:
        get_info_ids = True

    if anonymized:
        name_suffix = "_h"
        text_suffix = "_m"
    else:
        name_suffix = ""
        text_sufix = ""

    output_columns = ['nodeID', 'nodeUserID', 'parentID', 'rootID', 'actionType', 'nodeTime',
                      'platform', 'has_URL', 'domain_linked', 'links_to_external']
    if get_info_ids:
        output_columns.append('informationIDs')

    print('Extracting fields...')

    # extract URLS then add: has_URL, links_to_external, domain_linked
    urls_in_text = data['text' + text_suffix].apply(lambda x: get_urls(x))
    data.loc[:, 'urls_linked'] = [[parse_url(y) for y in x] for x in urls_in_text]
    data.loc[:, 'has_URL'] = [int(len(x) > 0) for x in data['urls_linked']]
    data.loc[:, 'domain_linked'] = [get_domains(x) for x in data['urls_linked']]
    data.loc[:, 'links_to_external'] = [has_link_external(domains, platform) for domains in data['domain_linked']]

    if len(keywords) > 0:
        data.loc[:, 'informationIDs'] = data['doc'].apply(
            lambda x: get_info_id_from_text([x['text' + text_suffix]], keywords))
    elif not info_id_fields is None:
        data.loc[:, 'informationIDs'] = pd.Series(
            [get_info_id_from_fields(c, info_id_fields, dict_field=True) for i, c in data.iterrows()])

    data = data.drop_duplicates('uid' + name_suffix)

    data.loc[:, 'actionType'] = ['message'] * len(data)

    data.loc[:, 'nodeTime'] = data['norm'].apply(lambda x: x['timestamp'])

    data.loc[:, 'communityID'] = data['doc'].apply(lambda x: x['peer']['username'] if 'peer' in x.keys() else None)

    data.loc[:, 'nodeID'] = data['doc'].apply(lambda x: str(x['to_id']['channel_id']) + '_' + str(x['id']))

    data.loc[:, 'nodeUserID'] = data['doc'].apply(
        lambda x: x['from_id' + name_suffix] if 'from_id' + name_suffix in x.keys() else None)
    data.loc[data['nodeUserID'].isnull(), 'nodeUserID'] = data.loc[data['nodeUserID'].isnull(), 'norm'].apply(
        lambda x: x['author'])

    data.loc[:, 'platform'] = platform

    data.loc[:, 'parentID'] = data['doc'].apply(lambda x: str(x['fwd_from']['channel_id']) + '_' + str(
        x['fwd_from']['channel_post']) if 'fwd_from' in x.keys() and not x['fwd_from'] is None and not x['fwd_from'][
                                                                                                           'channel_id'] is None and not
                                          x['fwd_from']['channel_post'] is None else None)

    data.loc[:, 'parentID'] = data['doc'].apply(lambda x: str(x['to_id']['channel_id']) + '_' + str(
        x['reply_to_msg_id']) if 'reply_to_msg_id' in x.keys() and not x['reply_to_msg_id'] is None else None)

    data.loc[:, 'rootID'] = '?'
    data.loc[data['parentID'].isna(), 'rootID'] = data.loc[data['parentID'].isna(), 'nodeID']

    data.loc[data['parentID'].isna(), 'parentID'] = data.loc[data['parentID'].isna(), 'nodeID']

    data = data[output_columns].copy()

    data = get_reply_cascade_root_tweet(data)

    print('Sorting...')
    data = data.sort_values('nodeTime').reset_index(drop=True)

    # initialize info ID column with empty lists
    data['threadInfoIDs'] = [[] for i in range(len(data))]

    # for some reason having a non-object column in the dataframe messes up the assignment of lists to individual cell values
    # remove it temporarily and add back later
    nodeTimes = data['nodeTime']
    data = data[[c for c in data.columns if c != 'nodeTime']]
    data['nodeTime'] = nodeTimes

    if get_info_ids:
        print('Adding information IDs to children...')
        # propagate infromation IDs to children
        finished = False
        count = 0
        while not finished:
            orig_info_ids = data['informationIDs'].copy()
            merged = data.reset_index().merge(data[['nodeID', 'informationIDs']], left_on='parentID',
                                              right_on='nodeID',
                                              suffixes=('', '_parent')).drop('nodeID_parent', axis=1).set_index("index")

            merged['informationIDs'] = (merged['informationIDs'] + merged['informationIDs_parent']).apply(
                lambda x: sorted(list(set(x))))

            data.loc[merged.index, 'informationIDs'] = merged['informationIDs']
            finished = (merged['informationIDs'] == orig_info_ids.loc[merged.index]).all()
            count += 1
            print('Iteration ', count, (merged['informationIDs'] != orig_info_ids.loc[merged.index]).sum(),
                  ' nodes to update')

        # remove items without informationIDs
        data = data[data['informationIDs'].str.len() > 0]

        print('Expanding events...')
        # expand lists of info IDs into seperate rows (i.e. an individual event is duplicated if it pertains to multiple information IDs)
        s = data.apply(lambda x: pd.Series(x['informationIDs']), axis=1).stack().reset_index(level=1, drop=True)
        s.name = 'informationID'

        data = data.drop('informationIDs', axis=1).join(s).reset_index(drop=True)
        # catch any additional empty string informationIDs
        data = data[data['informationID'] != ''].copy()

    data = data.drop('threadInfoIDs', axis=1)
    data = data.sort_values('nodeTime').reset_index(drop=True)
    data = convert_timestamps(data)
    data = data[~data['communityID'].isnull()]

    data['nodeUserID'] = data['nodeUserID'].replace(username_map)

    print('Done!')
    return data


def extract_reddit_data(fn='reddit_data.json',
                        info_id_fields=None,
                        keywords=[],
                        anonymized=False,
                        username_map={},
                        additional_fields=[],
                        propagate_info_ids=False):
    """
    Extracts fields from Reddit JSON data
    :param fn: A filename or list of filenames which contain the JSON Reddit data
    :param info_id_fields: A list of field paths from which to extract the information IDs. If None, don't extract any.
    """

    platform = 'reddit'
    json_data = load_json(fn)
    data = pd.DataFrame(json_data)

    get_info_ids = False
    if not info_id_fields is None or len(keywords) > 0:
        get_info_ids = True

    if anonymized:
        name_suffix = "_h"
        text_suffix = "_m"
    else:
        name_suffix = ""
        text_suffix = ""

    output_columns = ['nodeID', 'nodeUserID', 'parentID', 'rootID', 'actionType',
                      'nodeTime', 'platform', 'has_URL', 'domain_linked', 'links_to_external'] + additional_fields
    if get_info_ids:
        output_columns.append('informationIDs')

    for textcol in ['body' + text_suffix, 'selftext' + text_suffix, 'title' + text_suffix]:
        if textcol not in data.columns:
            data.loc[:, textcol] = np.nan

    print('Extracting fields...')
    data['text'] = data['body' + text_suffix].replace(np.nan, '', regex=True) + data['selftext' + text_suffix].replace(
        np.nan, '', regex=True) + data['title' + text_suffix].replace(np.nan, '', regex=True)

    # extract URLS then add: has_URL, links_to_external, domain_linked
    urls_in_text = data['text'].apply(lambda x: get_urls(x))
    data.loc[:, 'urls_linked'] = [[parse_url(y) for y in x] for x in urls_in_text]
    data.loc[:, 'has_URL'] = [int(len(x) > 0) for x in data['urls_linked']]
    data.loc[:, 'domain_linked'] = [get_domains(x) for x in data['urls_linked']]
    data.loc[:, 'links_to_external'] = [has_link_external(domains, platform) for domains in data['domain_linked']]

    if len(keywords) > 0:
        data.loc[:, 'informationIDs'] = data['text'].apply(lambda x: get_info_id_from_text([x], keywords))
    elif not info_id_fields is None:
        data.loc[:, 'informationIDs'] = pd.Series(
            [get_info_id_from_fields(c, info_id_fields) for i, c in data.iterrows()])
        data['n_info_ids'] = data['informationIDs'].apply(len)

    data = data.drop_duplicates('id' + name_suffix)

    data.rename(columns={'id' + name_suffix: 'nodeID', 'author' + name_suffix: 'nodeUserID',
                         'created_utc': 'nodeTime', 'parent_id' + name_suffix: 'parentID',
                         'link_id' + name_suffix: 'rootID'}, inplace=True)

    data.loc[:, 'actionType'] = ['comment'] * len(data)
    data.loc[~data["title_m"].isnull(), 'actionType'] = 'post'

    data.loc[data['actionType'] == "comment", 'nodeID'] = ['t1_' + x for x in
                                                           data.loc[data['actionType'] == "comment", 'nodeID']]
    data.loc[data['actionType'] == "post", 'nodeID'] = ['t3_' + x for x in
                                                        data.loc[data['actionType'] == "post", 'nodeID']]

    data.loc[data['actionType'] == "post", 'rootID'] = data.loc[data['actionType'] == "post", 'nodeID']
    data.loc[data['actionType'] == "post", 'parentID'] = data.loc[data['actionType'] == "post", 'nodeID']

    data.loc[:, 'communityID'] = data['subreddit_id']

    data.loc[:, 'platform'] = platform

    print('Sorting...')
    data = data.sort_values('nodeTime').reset_index(drop=True)

    data = data[output_columns].copy()

    # initialize info ID column with empty lists
    data['threadInfoIDs'] = [[] for i in range(len(data))]

    # for some reason having a non-object column in the dataframe messes up the assignment of lists to individual cell values
    # remove it temporarily and add back later
    nodeTimes = data['nodeTime']
    data = data[[c for c in data.columns if c != 'nodeTime']]

    data['nodeTime'] = nodeTimes

    if propagate_info_ids and get_info_ids:
        data["propagated_informationIDs"] = data["informationIDs"]
        print('Adding information IDs to children...')
        # propagate infromation IDs to children
        finished = False
        count = 0
        while not finished:
            orig_info_ids = data['propagated_informationIDs'].copy()
            merged = data.reset_index().merge(data[['nodeID', 'propagated_informationIDs']], left_on='parentID',
                                              right_on='nodeID',
                                              suffixes=('', '_parent')).drop('nodeID_parent', axis=1).set_index("index")

            merged['propagated_informationIDs'] = (merged['propagated_informationIDs'] + merged['propagated_informationIDs_parent']).apply(
                lambda x: sorted(list(set(x))))

            data.loc[merged.index, 'propagated_informationIDs'] = merged['propagated_informationIDs']
            finished = (merged['propagated_informationIDs'] == orig_info_ids.loc[merged.index]).all()
            count += 1
            print('Iteration ', count, (merged['propagated_informationIDs'] != orig_info_ids.loc[merged.index]).sum(),
                  ' nodes to update')

    if get_info_ids:
        # remove items without informationIDs
        data = data[data['informationIDs'].str.len() > 0]

        print('Expanding events...')
        # expand lists of info IDs into seperate rows
        # (i.e. an individual event is duplicated if it pertains to multiple information IDs)
        s = data.apply(lambda x: pd.Series(x['informationIDs']), axis=1).stack().reset_index(level=1, drop=True)
        s.name = 'informationID'

        data = data.drop('informationIDs', axis=1).join(s).reset_index(drop=True)
        # catch any additional empty string informationIDs
        data = data[data['informationID'] != ''].copy()

    data = data.drop('threadInfoIDs', axis=1)
    data = data.sort_values('nodeTime').reset_index(drop=True)
    data = convert_timestamps(data)

    data['nodeUserID'] = data['nodeUserID'].replace(username_map)

    print('Done!')
    return data


def extract_twitter_data(fn='twitter_data.json',
                         info_id_fields=None,
                         keywords=[],
                         anonymized=False,
                         username_map={},
                         additional_fields=[],
                         propagate_info_ids=False):
    """
    Extracts fields from Twitter JSON data
    :param fn: A filename or list of filenames which contain the JSON Twitter data
    :param info_id_fields: A list of field paths from which to extract the information IDs. If None, don't extract any.
    :param keywords:
    :params anonymized: Whether the data is in raw Twitter API format (False) or if it is in the processed and anonymized SocialSim data format (True).  The anonymized format has several modifications to field names.
    """

    platform = 'twitter'
    json_data = load_json(fn)
    data = pd.DataFrame(json_data)

    get_info_ids = False
    if not info_id_fields is None or len(keywords) > 0:
        get_info_ids = True

    if anonymized:
        name_suffix = "_h"
        text_suffix = "_m"
    else:
        name_suffix = ""
        text_suffix = ""

    data = data.sort_values("timestamp_ms").reset_index(drop=True)
    output_columns = ['nodeID', 'nodeUserID', 'parentID', 'rootID', 'actionType', 'nodeTime',
                      'partialParentID', 'platform', 'has_URL', 'domain_linked', 'links_to_external', 'urls_linked'] + additional_fields
    if get_info_ids:
        output_columns.append('informationIDs')

    #print('Extracting fields...')
    tweets = data
    #print("Just loaded",len(tweets), 883)

    # extract URLS then add: has_URL, links_to_external, domain_linked
    urls_in_text = get_twitter_urls(tweets, name_suffix)
    tweets.loc[:, 'urls_linked'] = [[parse_url(y) for y in x] for x in urls_in_text]
    tweets.loc[:, 'has_URL'] = [int(len(x) > 0) for x in tweets['urls_linked']]
    tweets.loc[:, 'domain_linked'] = [get_domains(x) for x in tweets['urls_linked']]
    tweets.loc[:, 'links_to_external'] = [has_link_external(domains, platform) for domains in tweets['domain_linked']]
    

    def get_full_text_if_exists(x):
        try:
            return x['full_text'+text_suffix]
        except:
            return ''

    def get_extended_full_text_if_exists(x, suffix):
        if not pd.isna(x):
            if "extended_tweet" in x.keys():
                full_tweet = x['extended_tweet']['full_text'+text_suffix]
            else:
                full_tweet = x["text{}".format(suffix)]
            return full_tweet
        else:
            return ""

    def get_as_full_text_as_possible(text, extendedtweet):
        extended_text = get_full_text_if_exists(extendedtweet)
        if len(extended_text) > len(text):
            return extended_text
        else:
            return text

    if 'extended_tweet' in tweets.columns:

        tweets.loc[:, 'text'] = [get_as_full_text_as_possible(text, extendedtweet) for text, extendedtweet in
                                 zip(tweets['text' + text_suffix], tweets['extended_tweet'])]
    else:
        tweets.loc[:, 'text'] = tweets['text' + text_suffix]

    if len(keywords) > 0:
        tweets.loc[:, 'informationIDs'] = tweets['text' + text_suffix].apply(
            lambda x: get_info_id_from_text([x], keywords))
    elif info_id_fields is not None:
        tweets.loc[:, 'informationIDs'] = pd.Series(
            [get_info_id_from_fields(t, info_id_fields) for i, t in tweets.iterrows()])
        tweets.loc[:, 'n_info_ids'] = tweets['informationIDs'].apply(len)
        tweets = tweets.sort_values('n_info_ids', ascending=False).reset_index(drop=True)
    
    tweets = tweets.drop_duplicates('id_str' + name_suffix)

    tweets.rename(columns={'id_str' + name_suffix: 'nodeID',
                           'timestamp_ms': 'nodeTime'}, inplace=True)
    #print("Added info ids")
    tweets.loc[:, 'platform'] = platform
    tweets.loc[:, 'nodeTime'] = pd.to_datetime(tweets['nodeTime'], unit='ms')
    tweets.loc[:, 'nodeTime'] = tweets['nodeTime'].apply(lambda x: datetime.strftime(x, '%Y-%m-%dT%H:%M:%SZ'))

    tweets.loc[:, 'nodeUserID'] = tweets['user'].apply(lambda x: x['id_str' + name_suffix])

    tweets.loc[:, 'is_reply'] = (tweets['in_reply_to_status_id_str' + name_suffix] != '') & (
        ~tweets['in_reply_to_status_id_str' + name_suffix].isna())

    if 'retweeted_status.in_reply_to_status_id_str' + name_suffix not in tweets:
        tweets.loc[:, 'retweeted_status.in_reply_to_status_id_str' + name_suffix] = ''
    if 'quoted_status.in_reply_to_status_id_str' + name_suffix not in tweets:
        tweets.loc[:, 'quoted_status.in_reply_to_status_id_str' + name_suffix] = ''
    if 'quoted_status.is_quote_status' not in tweets:
        tweets.loc[:, 'quoted_status.is_quote_status'] = False
    if 'quoted_status' not in tweets:
        tweets.loc[:, 'quoted_status'] = None

    # keep track of specific types of reply chains (e.g. retweet of reply, retweet of quote of reply) because the parents and roots will be assigned differently
    tweets.loc[:, 'is_retweet_of_reply'] = (~tweets[
        'retweeted_status.in_reply_to_status_id_str' + name_suffix].isna()) & (~(
                tweets['retweeted_status.in_reply_to_status_id_str' + name_suffix] == ''))
    tweets.loc[:, 'is_retweet_of_quote'] = (~tweets['retweeted_status'].isna()) & (~tweets['quoted_status'].isna()) & (
                tweets['quoted_status.in_reply_to_status_id_str' + name_suffix] == '')
    tweets.loc[:, 'is_retweet_of_quote_of_reply'] = (~tweets['retweeted_status'].isna()) & (
        ~tweets['quoted_status'].isna()) & (~(tweets['quoted_status.in_reply_to_status_id_str' + name_suffix] == ''))
    tweets.loc[:, 'is_retweet'] = (~tweets['retweeted_status'].isna()) & (~tweets['is_retweet_of_reply']) & (
        ~tweets['is_retweet_of_quote']) & (~tweets['is_retweet_of_quote_of_reply'])

    tweets.loc[:, 'is_quote_of_reply'] = (~tweets['quoted_status.in_reply_to_status_id_str' + name_suffix].isna()) & (
        ~(tweets['quoted_status.in_reply_to_status_id_str' + name_suffix] == '')) & (tweets['retweeted_status'].isna())
    tweets.loc[:, 'is_quote_of_quote'] = (~tweets['quoted_status.is_quote_status'].isna()) & (
                tweets['quoted_status.is_quote_status'] == True) & (tweets['retweeted_status'].isna())
    tweets.loc[:, 'is_quote'] = (~tweets['quoted_status'].isna()) & (~tweets['is_quote_of_reply']) & (
        ~tweets['is_quote_of_quote']) & (tweets['retweeted_status'].isna()) & (~tweets['is_reply'])

    tweets.loc[:, 'is_orig'] = (~tweets['is_reply']) & (~tweets['is_retweet']) & (~tweets['is_quote']) & (
        ~tweets['is_quote_of_reply']) & (~tweets['is_quote_of_quote']) & (~tweets['is_retweet_of_reply']) & (
                                   ~tweets['is_retweet_of_quote_of_reply']) & (~tweets['is_retweet_of_quote'])

    tweet_types = ['is_reply', 'is_retweet', 'is_quote', 'is_orig', 'is_retweet_of_reply', 'is_retweet_of_quote',
                   'is_retweet_of_quote_of_reply', 'is_quote_of_reply', 'is_quote_of_quote']
    to_concat = []

    replies = tweets[tweets['is_reply']].copy()
    if len(replies) > 0:
        # for replies we know immediate parent but not root
        replies.loc[:, 'actionType'] = 'reply'
        replies.loc[:, 'parentID'] = tweets['in_reply_to_status_id_str' + name_suffix]
        replies.loc[:, 'rootID'] = '?'
        replies.loc[:, 'partialParentID'] = tweets['in_reply_to_status_id_str' + name_suffix]

        to_concat.append(replies)
        
    retweets = tweets[(tweets['is_retweet']) & (~tweets['is_quote'])].copy()
    if len(retweets) > 0:
        # for retweets we know the root but not the immediate parent
        retweets.loc[:, 'actionType'] = 'retweet'
        retweets.loc[:, 'rootID'] = retweets['retweeted_status'].apply(lambda x: x['id_str' + name_suffix])
        retweets.loc[:, 'parentID'] = '?'
        retweets.loc[:, 'partialParentID'] = retweets['retweeted_status'].apply(lambda x: x['id_str' + name_suffix])

        to_concat.append(retweets)
    
    retweets_of_replies = tweets[tweets['is_retweet_of_reply']].copy()
    if len(retweets_of_replies) > 0:
        # for retweets of replies the "root" is actually the reply not the ultimate root
        # the parent of a retweet of a reply will be the reply or any retweet of the reply
        # the root can be retraced by following parents up the tree
        retweets_of_replies.loc[:, 'parentID'] = '?'
        retweets_of_replies.loc[:, 'rootID'] = '?'
        retweets_of_replies.loc[:, 'partialParentID'] = retweets_of_replies['retweeted_status'].apply(
            lambda x: x['in_reply_to_status_id_str' + name_suffix])
        retweets_of_replies.loc[:, 'actionType'] = 'retweet'

        to_concat.append(retweets_of_replies)

    retweets_of_quotes = tweets[tweets['is_retweet_of_quote']].copy()
    if len(retweets_of_quotes) > 0:
        # for retweets of quotes we know the root (from the quoted status) but not the parent
        # the parent will be either the quote or any retweets of it
        retweets_of_quotes.loc[:, 'parentID'] = '?'
        retweets_of_quotes.loc[:, 'rootID'] = retweets_of_quotes['quoted_status'].apply(
            lambda x: x['id_str' + name_suffix])
        retweets_of_quotes.loc[:, 'partialParentID'] = retweets_of_quotes['retweeted_status'].apply(
            lambda x: x['id_str' + name_suffix])
        retweets_of_quotes.loc[:, 'actionType'] = 'retweet'

        to_concat.append(retweets_of_quotes)
        
    retweets_of_quotes_of_replies = tweets[tweets['is_retweet_of_quote_of_reply']].copy()
    if len(retweets_of_quotes_of_replies) > 0:
        # for retweets of quotes of replies we don't know the root or the parent. the quoted status refers back to the reply not the final root
        # the parent will be either the quote or a retweet of the quote
        # we can find the root by tracking parents up the tree
        retweets_of_quotes_of_replies.loc[:, 'parentID'] = '?'
        retweets_of_quotes_of_replies.loc[:, 'rootID'] = '?'
        retweets_of_quotes_of_replies.loc[:, 'partialParentID'] = retweets_of_quotes_of_replies['quoted_status'].apply(
            lambda x: x['id_str' + name_suffix])
        retweets_of_quotes_of_replies.loc[:, 'actionType'] = 'retweet'

        to_concat.append(retweets_of_quotes_of_replies)
        
    quotes = tweets[tweets['is_quote']].copy()
    if len(quotes) > 0:
        # for quotes we know the root but not the parent
        quotes.loc[:, 'actionType'] = 'quote'
        quotes.loc[:, 'rootID'] = quotes['quoted_status'].apply(lambda x: x['id_str' + name_suffix])
        quotes.loc[:, 'parentID'] = '?'
        quotes.loc[:, 'partialParentID'] = quotes['quoted_status'].apply(lambda x: x['id_str' + name_suffix])

        to_concat.append(quotes)
        
    quotes_of_replies = tweets[tweets['is_quote_of_reply']].copy()
    if len(quotes_of_replies) > 0:
        # for quotes of replies we don't know the root or the parent
        # the parent will be the reply or any retweets of the reply
        # the root can be tracked back using the parents in the tree
        quotes_of_replies.loc[:, 'parentID'] = '?'
        quotes_of_replies.loc[:, 'rootID'] = '?'
        quotes_of_replies.loc[:, 'partialParentID'] = quotes_of_replies['quoted_status'].apply(
            lambda x: x['in_reply_to_status_id_str' + name_suffix])
        quotes_of_replies.loc[:, 'actionType'] = 'quote'

        to_concat.append(quotes_of_replies)
        
    quotes_of_quotes = tweets[tweets['is_quote_of_quote']].copy()
    if len(quotes_of_quotes) > 0:
        # for quotes of quotes we don't know the parent or the root
        # the parent will be the first quote or any retweets of it
        # the root can be traced back through the parent tree
        quotes_of_quotes.loc[:, 'parentID'] = '?'
        quotes_of_quotes.loc[:, 'rootID'] = '?'
        quotes_of_quotes.loc[:, 'partialParentID'] = quotes_of_quotes['quoted_status'].apply(
            lambda x: x['quoted_status_id_str'])
        quotes_of_quotes.loc[:, 'actionType'] = 'quote'

        to_concat.append(quotes_of_quotes)
        
    orig_tweets = tweets[tweets['is_orig']].copy()
    if len(orig_tweets) > 0:
        # for original tweets assign parent and root to be itself
        orig_tweets.loc[:, 'actionType'] = 'tweet'
        orig_tweets.loc[:, 'parentID'] = orig_tweets['nodeID']
        orig_tweets.loc[:, 'rootID'] = orig_tweets['nodeID']
        orig_tweets.loc[:, 'partialParentID'] = orig_tweets['nodeID']
        to_concat.append(orig_tweets)
        
    tweets = pd.concat(to_concat, ignore_index=True, sort=False)
    tweets['nodeID'] = tweets['nodeID'].astype(str)
    tweets = tweets[output_columns]
    tweets = tweets.sort_values("nodeTime").reset_index(drop=True)

    #print('Reconstructing cascades...')
    tweets = full_reconstruction(tweets)
    # initialize info ID column with empty lists
    tweets['threadInfoIDs'] = [[] for i in range(len(tweets))]

    tweets = tweets.reset_index(drop=True)

    if propagate_info_ids and get_info_ids:
        tweets["propagated_informationIDs"] = tweets["informationIDs"]
        print('Adding information IDs to children...')
        # propagate information IDs to children
        finished = False
        count = 0
        while not finished:
            orig_info_ids = tweets['propagated_informationIDs'].copy()
            merged = tweets.reset_index().merge(tweets[['nodeID', 'propagated_informationIDs']], left_on='parentID',
                                                right_on='nodeID',
                                                suffixes=('', '_parent')).drop('nodeID_parent', axis=1).set_index(
                "index")
            merged['propagated_informationIDs'] = (merged['propagated_informationIDs'] + merged['propagated_informationIDs_parent']).apply(
                lambda x: sorted(list(set(x))))
            tweets.loc[merged.index, 'propagated_informationIDs'] = merged['propagated_informationIDs']
            finished = (merged['propagated_informationIDs'] == orig_info_ids.loc[merged.index]).all()
            count += 1
            print('Iteration ', count, (merged['propagated_informationIDs'] != orig_info_ids.loc[merged.index]).sum(),
                  ' nodes to update')
    
    if get_info_ids:
        # remove tweets with no informationID
        tweets = tweets[tweets['informationIDs'].str.len() > 0]

        print('Expanding events...')
        # expand lists of info IDs into seperate rows (i.e. an individual event is duplicated if it pertains to multiple information IDs)
        s = tweets.apply(lambda x: pd.Series(x['informationIDs']), axis=1).stack().reset_index(level=1, drop=True)
        s.name = 'informationID'
        tweets = tweets.drop(['informationIDs', 'partialParentID'], axis=1).join(s).reset_index(drop=True)
        # catch any additional empty string informationIDs
        tweets = tweets[tweets['informationID'] != ''].copy()

    tweets = tweets.drop('threadInfoIDs', axis=1)
    tweets = convert_timestamps(tweets)

    if len(username_map) > 0:
        tweets['nodeUserID'] = tweets['nodeUserID'].replace(username_map)

    print('Done!')
    return tweets


def get_github_text_field(row):
    github_text_fields = {"PushEvent": ["commits", "message_m"],
                          "PullRequestEvent": ["pull_request", "body_m"],
                          "IssuesEvent": ["issue", "body_m"],
                          "CreateEvent": ["description_m"],
                          "PullRequestReviewCommentEvent": ["comment", "body_m"],
                          "ForkEvent": ["forkee", "description_m"],
                          "IssueCommentEvent": ["comment", "body_m"],
                          "CommitCommentEvent": ["comment", "body_m"]}

    if row['actionType'] not in github_text_fields.keys():
        return ''

    if row['actionType'] == 'PushEvent':
        text = ' '.join(c['message_m'] for c in row['payload']['commits'])
    else:
        text = row['payload']

        for f in github_text_fields[row['actionType']]:
            if f in text:
                text = text[f]
            else:
                text = ''

    return text


def extract_github_data(fn='github_data.json',
                        info_id_fields=None,
                        keywords=[],
                        anonymized=False,
                        username_map={},
                        additional_fields=[]):
    platform = 'github'
    json_data = load_json(fn)
    data = pd.DataFrame(json_data)

    get_info_ids = False
    if not info_id_fields is None or len(keywords) > 0:
        get_info_ids = True

    if anonymized:
        name_suffix = "_h"
        text_suffix = "_m"
    else:
        name_suffix = ""
        text_suffix = ""

    github_text_fields = {"PushEvent": ["commits", "message" + text_suffix],
                          "PullRequestEvent": ["pull_request", "body" + text_suffix],
                          "IssuesEvent": ["issue", "body" + text_suffix],
                          "CreateEvent": ["description" + text_suffix],
                          "PullRequestReviewCommentEvent": ["comment", "body" + text_suffix],
                          "ForkEvent": ["forkee", "description" + text_suffix],
                          "IssueCommentEvent": ["comment", "body" + text_suffix],
                          "CommitCommentEvent": ["comment", "body" + text_suffix]}

    print('Extracting fields...')
    output_columns = ['nodeID', 'nodeUserID', 'actionType', 'nodeTime', 'platform',
                      'has_URL', 'domain_linked', 'links_to_external'] + additional_fields
    if get_info_ids:
        output_columns.append('informationIDs')

    if 'event' in data.columns:
        data.loc[:, 'nodeTime'] = data['event'].apply(lambda x: x['created_at'])
        data.loc[:, 'actionType'] = data['event'].apply(lambda x: x['type'])
        data.loc[:, 'nodeUserID'] = data['event'].apply(lambda x: x['actor']['login' + name_suffix])
        data.loc[:, 'nodeID'] = data['event'].apply(lambda x: x['repo']['name' + name_suffix])
    else:
        data.loc[:, 'nodeUserID'] = data['actor'].apply(lambda x: x['login' + name_suffix])
        data.loc[:, 'nodeID'] = data['repo'].apply(lambda x: x['name' + name_suffix])

        data.rename(columns={'created_at': 'nodeTime',
                             'type': 'actionType'}, inplace=True)

    data.loc[:, 'platform'] = platform

    def get_text_field(row):

        if row['actionType'] not in github_text_fields.keys():
            return ''

        if row['actionType'] == 'PushEvent':
            text = ' '.join(c['message' + text_suffix] for c in row['payload']['commits'])
        else:
            text = row['payload']

            for f in github_text_fields[row['actionType']]:
                if f in text:
                    text = text[f]
                else:
                    text = ''

        return text

    # extract URLS then add: has_URL, links_to_external, domain_linked
    urls_in_text = data.apply(get_text_field, axis=1).apply(lambda x: get_urls(x))
    data.loc[:, 'urls_linked'] = [[parse_url(y) for y in x] for x in urls_in_text]
    data.loc[:, 'has_URL'] = [int(len(x) > 0) for x in data['urls_linked']]
    data.loc[:, 'domain_linked'] = [get_domains(x) for x in data['urls_linked']]
    data.loc[:, 'links_to_external'] = [has_link_external(domains, platform) for domains in data['domain_linked']]

    if len(keywords) > 0:
        data.loc[:, 'text_field'] = data.apply(get_text_field, axis=1)
        data = data.dropna(subset=['text_field'])
        data.loc[:, 'informationIDs'] = data['text_field'].apply(lambda x: get_info_id_from_text([x], keywords))
        data = data.drop('text_field', axis=1)
    elif not info_id_fields == None:
        if 'socialsim_details' in data.columns:
            data.loc[:, 'informationIDs'] = pd.Series(data['socialsim_details'].apply(
                lambda x: list(itertools.chain.from_iterable([get_info_id_from_fields(m, info_id_fields) for m in x]))))
        else:
            data.loc[:, 'informationIDs'] = pd.Series(
                [get_info_id_from_fields(t, info_id_fields) for i, t in data.iterrows()])

    events = data[output_columns]

    events = events[events.actionType.isin(
        ['PullRequestEvent', 'IssuesEvent', 'CreateEvent', 'DeleteEvent', 'WatchEvent', 'ForkEvent',
         'PullRequestReviewCommentEvent', 'CommitCommentEvent', 'PushEvent', 'IssueCommentEvent'])]

    if get_info_ids:
        print('Expanding events...')
        # expand lists of info IDs into seperate rows (i.e. an individual event is duplicated if it pertains to multiple information IDs)
        s = events.apply(lambda x: pd.Series(x['informationIDs']), axis=1).stack().reset_index(level=1, drop=True)
        s.name = 'informationID'
        events = events.drop('informationIDs', axis=1).join(s).reset_index(drop=True)
        events = events.dropna(subset=['informationID'])

    events = convert_timestamps(events)

    events = events.drop_duplicates([c for c in events.columns if c != 'domain_linked'])

    print('Done!')
    events['nodeUserID'] = events['nodeUserID'].replace(username_map)
    return events
