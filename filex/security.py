import hashlib


def md5(in_str):
    m = hashlib.md5()
    m.update(in_str.encode('utf-8'))
    return m.hexdigest()


def make_share_string(in_str, salt):
    query = in_str + "-" + salt + "-" + md5(in_str)
    query = md5(query)[-5:]
    query_fin = in_str + "-" + query
    return query_fin


def check_share_string(in_list, salt):
    str_0 = str(int(in_list[0]))
    str_1 = str(int(in_list[1]))
    checksum = in_list[2]
    query = str_0 + "-" + str_1 + "-" + salt + "-" + md5(str_0 + "-" + str_1)
    query = md5(query)[-5:]
    return checksum == query
