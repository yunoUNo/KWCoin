from subprocess import PIPE,Popen
import os
import shlex
import tempfile
import click


def dump_database(hostname, port, database, username, password, dstfile):
    cmd = 'pg_dump -h %s -p %s -U %s -f %s -d %s'  % (hostname, port, username, dstfile, database)
    cmd = shlex.split(cmd)
    local_env = os.environ.copy()
    local_env["PGPASSWORD"] = password
    p = Popen(cmd, shell=False, env=local_env, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    return p.communicate()

def restore_database(hostname, port, database, username, password, srcfile):
    cmd = 'psql -h %s -p %s -U %s -d %s -f %s' % (hostname, port, username, database, srcfile)
    cmd = shlex.split(cmd)
    local_env = os.environ.copy()
    local_env["PGPASSWORD"] = password
    p = Popen(cmd, shell=False,  env=local_env, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    return p.communicate()

def get_temp():
    f = tempfile.NamedTemporaryFile(delete=False)
    name = f.name
    f.close
    return name

def remove_temp(f_name):
    return os.unlink(f_name)

def apply_regex(f, regex):
    cmd = 'sed -i ''%s'' %s' % (regex, f)    
    cmd = shlex.split(cmd)
    p = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    return p.communicate()