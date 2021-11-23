#!/usr/bin/python3

# Copyright 2017 ClearDATA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0

import os
import configparser
import shutil
import sys
import time

import boto3
import botocore

session = boto3.session.Session()
sts = session.client('sts')
iam = session.client('iam')


def main():
    r = sts.get_caller_identity()
    iamobj = r['Arn'].split(':')[-1]
    if not iamobj.startswith('user/'):
        print(
            '''ERROR: This script is only useful for profiles with an IAM user.
Your current AWS identity does not look like an IAM user:
  %s
Perhaps you meant to select another profile? ''' % r['Arn'],
            file=sys.stderr,
        )
        sys.exit(1)

    # load old credentials
    fname = os.path.join(os.environ['HOME'], '.aws', 'credentials')
    config = configparser.ConfigParser()
    config.read(fname)

    if session.profile_name not in config.sections():
        raise ValueError('No profile %s in credentials' % session.profile_name)

    # backup, stash old creds
    old_umask = os.umask(0o077)
    shutil.copyfile(fname, fname + '.old')
    os.umask(old_umask)
    old_access_key = config.get(session.profile_name, 'aws_access_key_id')
    print('created backup of credentials file at %s' % fname + '.old')

    # get new key and save
    username = iamobj.split('/')[1]
    r = iam.create_access_key(UserName=username)
    key = r['AccessKey']
    print('generated a new access key with id %s' % key['AccessKeyId'])

    config.set(
        session.profile_name,
        'aws_access_key_id',
        key['AccessKeyId'],
    )
    config.set(
        session.profile_name,
        'aws_secret_access_key',
        key['SecretAccessKey'],
    )

    with open(fname, 'w') as f:
        config.write(f)

    # create a new session to load new credentials
    new_session = boto3.session.Session()
    new_iam = new_session.client('iam')

    # delete previous access key, but retry since IAM might not be caught up
    print('cleaning up old access key with id %s' % old_access_key,
          end='', flush=True)
    n = 0
    while True:
        try:
            new_iam.delete_access_key(UserName=username,
                                      AccessKeyId=old_access_key)
            print('success!')
            return

        except botocore.exceptions.ClientError:
            print('.', end='', flush=True)
            time.sleep(2**n / 10.0)
            n += 1

            if n > 8:
                raise ValueError('Exceeded max retries while deleting %s' % old_access_key)


if __name__ == '__main__':
    main()
