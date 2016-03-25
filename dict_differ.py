#!/usr/bin/env python
import argparse
import yaml


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict = current_dict.copy()
        self.past_dict = past_dict.copy()
        self.set_current = set(current_dict.keys())
        self.set_past = set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
        for k, v in self.past_dict.items():
            if type(v) is list:
                v.sort()
                self.past_dict[k] = v
        for k, v in self.current_dict.items():
            if type(v) is list:
                v.sort()
                self.current_dict[k] = v

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def unchanged(self):
        return set(o for o in self.intersect
                   if self.past_dict[o] == self.current_dict[o])

    def changed(self):
        changed = [k for k in self.intersect
                   if self.past_dict[k] != self.current_dict[k]]

        if len(changed) == 0:
            return set()
        else:
            diff_curr = {k: v for k, v in self.current_dict.items()
                         if k in changed}
            diff_pass = {k: v for k, v in self.past_dict.items()
                         if k in changed}

            (diff_result, ok) = walk(diff_curr, diff_pass)

            return diff_result


def walk(node1, node2, parent_name=''):
    """Walk through each node in tree and compare difference"""

    diff_results = []

    if type(node1) != type(node2):
        return (["[Type] {} vs {}".format(node1, node2)], False)

    elif type(node1) not in [list, dict] and type(node2) not in [list, dict]:
        return (["[Value] {} vs {}".format(node1, node2)], False)

    elif type(node1) is dict and type(node2) is dict:
        for k in [x for x in node1.keys() if x not in node2.keys()]:
            diff_results.append("[Key added] {}".format(k))
            node1.pop(k)

        for k in [x for x in node2.keys() if x not in node1.keys()]:
            diff_results.append("[Key removed] {}".format(k))
            node2.pop(k)

        # Dict same length, with same keys
        for k, v in node1.items():
            if v == node2[k]:
                continue

            if type(v) not in [list, dict] or \
                    type(node2[k]) not in [list, dict]:
                diff_results.append(
                    "[Dict] key '{}' value conflict: {} != {}".format(
                        k, v, node2[k]))
            else:
                (walk_result, ok) = walk(node1[k],
                                         node2[k],
                                         '/'.join([parent_name, k]))
                if not ok:
                    diff_results.append(walk_result)

    elif type(node1) is list and type(node2) is list:

        # Find the different items in both lists
        intersect = [x for x in node1 if x in node2]
        node1 = [x for x in node1 if x not in intersect]
        node2 = [x for x in node2 if x not in intersect]

        if len(node1) != len(node2):
            diff_results.append(
                "[List length different] {}, {} vs {}".format(
                    parent_name, len(node1), len(node2)))

            return (diff_results, False)

        for k in range(len(node1)):
            v1 = node1[k]
            v2 = node2[k]

            if type(v1) != type(v2):
                diff_results.append(
                    "[List item type][{}] {} != {}".format(
                        parent_name, type(v1), type(v2)))

            elif type(v1) not in [list, dict] or type(v2) not in [list, dict]:
                diff_results.append(
                    "[List][{}] value conflict: {} != {}".format(
                        '/'.join([parent_name, "[{}]".format(k)]), v1, v2))

            else:
                (walk_result, ok) = walk(v1, v2, '/'.join([parent_name,
                                                           "[{}]".format(k)]))

                if not ok:
                    diff_results.append(walk_result)

    if len(diff_results) == 0:
        return ([], True)
    else:
        return (diff_results, False)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("file",
                        nargs='*',
                        help="Which files to compare?",
                        type=str)

    args = parser.parse_args()

    try:
        dict_curr = yaml.load(open(args.file[0]))
        dict_past = yaml.load(open(args.file[1]))
    except:
        msg = "You must assign two files! Sample usage:\n"
        msg += "lib/debug.py result_test.json, result_sta.json"
        raise Exception(msg)

    d = DictDiffer(dict_curr, dict_past)

    print "Items added to the dict:", yaml.dump(d.added())
    print "Items removed to the dict:", yaml.dump(d.removed())
    print "Items unchanged to the dict:", yaml.dump(d.unchanged())
    print "Items changed to the dict:\n", yaml.dump(d.changed())
