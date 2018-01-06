# -*- coding:utf-8 -*-

import ConfigParser


class ConfigReader:

    conf = ConfigParser.ConfigParser()
    conf.read('conf.ini')

    @classmethod
    def read_conf(cls):
        cls.conf.read('conf.ini')

    @classmethod
    def get_member_room_number(cls, name):
        return cls.conf.get('juju_room', name)

    @classmethod
    def get_qq_number(cls, name):
        return cls.conf.get('qq_conf', name)

    @classmethod
    def get_group_number(cls):
        return cls.conf.get('qq_conf', 'group_number')

    @classmethod
    def get_test_group_number(cls):
        return cls.conf.get('qq_conf', 'test_group_number')

    @classmethod
    def get_property(cls, root, name):
        return cls.conf.get(root, name)

    @classmethod
    def get_group_name(cls, number):
        return cls.conf.get('qq_conf', number)


if __name__ == '__main__':
    print ConfigReader.get_member_room_number('fengxiaofei')
