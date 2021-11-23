# awskeyrot

`awskeyrot` rotates an AWS IAM user's access keys.  It loads the credentials for a configured profile, tries to pivot to a newly created key, and deletes the old one if successful.

This has been tested on Linux and Mac; it should work on any Unix-like system.  I don't know if it would work on Windows.

It only depends on `boto3` and `botocore`; nearly any version should suffice.

## install

Install to any location in your PATH:

    install -D awskeyrot.py ~/.local/bin

You can use a system interpreter, for example on Debian, like this:

    sudo apt install python3-boto python3-botocore

If you're running from a venv, you probably want to do this instead:

    python3 -m pip install -r requirements.txt

## manual rotation

If your default AWS profile uses an IAM user you can just run `awskeyrot.py`.  Otherwise, you can specify the profile using the `AWS_PROFILE` environment variable.  For example:

    $ AWS_PROFILE=cdn awskeyrot.py
    created backup of credentials file at /home/ross/.aws/credentials.old
    generated a new access key with id AKIA33H4LE4GINYMU64V
    cleaning up old access key with id AKIA33H4LE4GDCQSPSVZ.......success!

## automatic rotation

### systemd

The `systemd` directory contains example service and timer unit templates for automating your key rotation.  The profile is set by the instance name.  To use:

To use with the `default` profile:

1. `install -m 0644 -D systemd/* ~/.local/share/systemd/user` (or another user path from `systemd.unit(5)`)
2. `systemctl --user daemon-reload`
3. `systemctl --user enable awskeyrot@default.timer --now`

To rotate other profiles, repeat the last step with a different profile name.

By default, your keys will be rotated weekly, with a randomized spread of up to four hours.  For info on customizing this, see `systemd.timer(5)`.
