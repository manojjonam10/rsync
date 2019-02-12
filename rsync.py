import argparse
import os
import filecmp
import shutil
import stat
import hashlib
import difflib
import io
from contextlib import redirect_stderr
import sys


def is_same(dir1, dir2):
    # Compare two directory trees content.
    compared = filecmp.dircmp(dir1, dir2)
    if (compared.left_only or compared.right_only or
       compared.diff_files or compared.funny_files):
        return False
    for subdir in compared.common_dirs:
        src = os.path.join(dir1, subdir)
        dst = os.path.join(dir2, subdir)
        if not is_same(src, dst):
            return False
    return True


def file_error_sub():
    print("rsync error: some files/attrs were not transferred"
          " (see previous errors) "
          "(code 23) at main.c(1209) [sender=3.1.3]")


def file_error_sub1():
    print("rsync error: error in file IO (code 11) "
          "at main.c(668) [Receiver=3.1.3]")


def file_error_sub2(pwd, a):
    print("rsync: ERROR: cannot stat destination "'"' + pwd + "/" + a
          + '"' + ": Not a directory (20)")


def file_error1(pt):
    print("rsync: send_files failed to open " + '"' + pt
          + '"' + ": Permission denied (13)")


def file_error3(pwd, a):
    print("rsync: change_dir" + '"' + pwd + "/" + a + '"'+" "
          + "failed: No such file or directory (2)")


def dir_error1(pt):
    print("rsync: opendir  " + '"' + pt
          + '"' + "." + "failed: "
          "Permission denied (13)")


def dir_error2(pt):
    print("rsync: mkdir" + " " + '"' + pt
          + '"' + " " + "failed: No such file or directory (2)")


def error_io():
    print("rsync error: errors selecting input/output files, "
          "dirs (code 3) at main.c(646) [Receiver=3.1.3]")


def directory_error():
    print('ERROR: destination must be a directory '
          'when copying more than 1 file')


def error_io1():
    print('rsync error: errors selecting input/output '
          'files, dirs (code 3) at main.c(634) [Receiver=3.1.3]')


def write_error(pt):
    print("rsync: mkstemp" + '"' + pt+" "+"failed: Permission denied (13)")


# copy non existing directory
def copy_directory(src, dst):
    try:
        shutil.copytree(src, dst, True)
    except EnvironmentError as e:
        print(e)



def getmtime(f):
    return os.path.getmtime(f)


def recursive_search(dir1, dir2, arg):
    if os.access(os.path.normpath(dir1), os.R_OK):

        for path, dirs, files in os.walk(dir1):
            if "/" in path:
                    ss = str(path)
                    p = len(dir1)+1
                    subs = os.path.join(ss[p:])
                    pt = os.path.join(os.getcwd(), arg.source)
                    if os.path.exists(os.path.join(dir2, subs)):
                        f = os.path.join(dir1, subs)
                        d = os.path.join(dir2, subs)
                        if os.access(f, os.R_OK):
                            comparison = filecmp.dircmp(f, d)
                            compare_different(comparison, f, d, arg)

                            if comparison.left_only:
                                for i in comparison.left_only:
                                    if os.path.isfile(os.path.join(f, i)):
                                        fx = os.path.join(f, i)
                                        dx = os.path.join(d, i)
                                        if os.access(fx, os.R_OK):
                                            if not check_index(dx):
                                                if os.path.islink(fx):
                                                    sym_link(fx, dx)

                                                elif check_innode(fx):
                                                    os.link(fx, dx)
                                                else:
                                                    try:
                                                        shutil.copy2(fx, dx)

                                                    except EnvironmentError:
                                                        print("Invalid action")
                                            else:
                                                file_error_sub2(os.getcwd(), d)
                                                error_io()

                                        else:
                                            file_error1(pt)
                                            file_error_sub()
                                    else:
                                        fc = os.path.join(f, i)
                                        if os.access(fc, os.R_OK):
                                            s = os.path.join(f, i)
                                            d = os.path.join(d, i)
                                            copy_directory(s, d)
                                        else:
                                            dir_error1(pt)
                                            file_error_sub()
                        else:
                            dir_error1(pt)
                            file_error_sub()
                    else:
                        s = os.path.join(dir1, subs)
                        d = os.path.join(dir2, subs)
                        if os.access(s, os.R_OK):
                            copy_directory(s, d)
                        else:
                            dir_error1(pt)
                            file_error_sub()
    else:
        pt = os.path.join(os.getcwd(), arg.source)
        dir_error1(pt)
        file_error_sub()


def recursive_searchx(dir1, dir2, src):
    if os.access(os.path.normpath(dir1), os.R_OK):

        for path, dirs, files in os.walk(dir1):
            if "/" in path:
                    ss = str(path)
                    p = len(dir1)
                    subs = os.path.join(ss[p:])
                    if subs[0:1] == "/":
                        p1 = len(dir1)+1
                        subs = os.path.join(ss[p1:])

                    pt = os.path.join(os.getcwd(), dir1)

                    if os.path.exists(os.path.join(dir2, subs)):
                        f = os.path.join(dir1, subs)
                        d = os.path.join(dir2, subs)

                        if os.access(f, os.R_OK):
                            comparison = filecmp.dircmp(f, d)
                            compare_differentx(comparison, f, d)

                            if comparison.left_only:
                                for i in comparison.left_only:
                                    if os.path.isfile(os.path.join(f, i)):
                                        fx = os.path.join(f, i)
                                        dx = os.path.join(d, i)

                                        if os.access(fx, os.R_OK):
                                            if not check_index(dx):
                                                if os.path.islink(fx):
                                                    sym_link(fx, dx)

                                                elif check_innode(fx):
                                                    os.link(fx, dx)
                                                else:
                                                    try:
                                                        shutil.copy2(fx, dx)

                                                    except EnvironmentError:
                                                        print("Invalid action")
                                            else:
                                                file_error_sub2(os.getcwd(), d)
                                                error_io()

                                        else:
                                            file_error1(pt)
                                            file_error_sub()
                                    elif os.path.isdir(os.path.join(f, i)):
                                        fc = os.path.join(f, i)
                                        if os.access(fc, os.R_OK):
                                            dm = os.path.join(d, i)
                                            if not os.path.exists(dm):
                                                s = os.path.join(f, i)
                                                d = os.path.join(d, i)
                                                copy_directory(s, d)
                                        else:
                                            dir_error1(pt)
                                            file_error_sub()
                        else:
                            dir_error1(pt)
                            file_error_sub()
                    else:
                        s = os.path.join(dir1, subs)
                        d = os.path.join(dir2, subs)
                        if os.access(s, os.R_OK):
                            copy_directory(s, d)
                        else:
                            dir_error1(pt)
                            file_error_sub()
    else:
        pt = os.path.join(os.getcwd(), src)
        dir_error1(pt)
        file_error_sub()


def is_hard_link(f, ss):
    s1 = os.stat(f)
    s2 = os.stat(ss)
    return (s1[stat.ST_INO], s1[stat.ST_DEV]) == \
           (s2[stat.ST_INO], s2[stat.ST_DEV])


def checksum(fp):
    # get the checksum of the file in md5 and return it
    with open(fp, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def run_arguments(f, ss, arg):
    # check and run for positional arguments
    if arg.permission:
        if oct(stat.S_IMODE(os.lstat(f).st_mode)) != \
                oct(stat.S_IMODE(os.lstat(ss).st_mode)):
            os.chmod(ss, stat.S_IMODE(os.lstat(f).st_mode))

    if arg.times:
        times = (os.path.getmtime(f))
        os.utime(ss, (times, times))


def run_argumentsx(f, ss):
    # check and run for positional arguments
    if oct(stat.S_IMODE(os.lstat(f).st_mode)) != \
            oct(stat.S_IMODE(os.lstat(ss).st_mode)):
        os.chmod(ss, stat.S_IMODE(os.lstat(f).st_mode))

    times = (os.path.getmtime(f))
    os.utime(ss, (times, times))

    if "-p" or "--permission" in sys.argv:
        if oct(stat.S_IMODE(os.lstat(f).st_mode)) != \
                oct(stat.S_IMODE(os.lstat(ss).st_mode)):
            os.chmod(ss, stat.S_IMODE(os.lstat(f).st_mode))

    if "-t" or "--times" in sys.argv:
        times = (os.path.getmtime(f))
        os.utime(ss, (times, times))


def check_innode(fx):
    f = os.stat(fx)
    if f[stat.ST_NLINK] > 1:
        return True
    else:
        return False


def check_index(s):
    f = str(s)
    fx = (f[len(f) - 1:])
    if "/" in fx:
        return True
    return False


def modify_file(f, ss):
    # compare difference between file and modify difference

    number_lines_f = sum(1 for line in open(f, 'r',
                         encoding="ISO-8859-1"))

    number_lines_ss = sum(1 for line in open(ss, 'r',
                          encoding="ISO-8859-1"))

    if number_lines_ss > number_lines_f:
        with open(ss, "r", encoding="ISO-8859-1") as dst:
            fss_text = dst.read().splitlines()
            with open(ss, "w") as dst1:
                for d, i in enumerate(fss_text):
                    if d < number_lines_f:
                        dst1.write("%s\n" % i)

    if number_lines_ss < number_lines_f:
        with open(f, "r", encoding="ISO-8859-1") as dst:
            fss_text = dst.read().splitlines()
            with open(ss, "a") as dst1:
                for d, i in enumerate(fss_text):
                    if d >= number_lines_ss-1:
                        dst1.write("%s\n" % i)

    ls = []

    with open(f, 'r', encoding="ISO-8859-1") as f1:
        f1_text = f1.read().splitlines()
    with open(ss, 'r', encoding="ISO-8859-1") as f2:

        f2_text = f2.read().splitlines()

        if len(f1_text) == len(f2_text):

            for d, i in enumerate(f2_text):
                x = i
                p = 0

                if x != f1_text[d]:
                        matcher = difflib.SequenceMatcher(None, i, f1_text[d])
                        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

                            sp = len(x)
                            if tag == 'replace':
                                if i1 == 0 and i2 + p < sp:
                                    x = f1_text[d][j1:j2] + x[i2 + p:]
                                elif i1 == 0 and i2 + p == sp:
                                    x = f1_text[d][j1:j2]
                                elif i1 > 0 and i2 + p < sp:
                                    x = x[:i1 + p] + f1_text[d][j1:j2] \
                                        + x[i2 + p:]
                                elif i1 > 0 and i2 + p == sp:
                                    x = x[:i1 + p] + f1_text[d][j1:j2]

                            if tag == 'delete':
                                if i1 == 0 and i2 + p < sp:
                                    x = x[i2 + p:]
                                elif i1 == 0 and i2 + p == sp:
                                    x = ""
                                elif i1 > 0 and i2 + p < sp:
                                    x = x[:i1 + p] + x[i2 + p:]
                                elif i1 > 0 and i2 + p == sp:
                                    x = x[:i1 + p]
                            if tag == 'insert':
                                if i1 == 0 and i2 + p < sp:
                                    x = f1_text[d][j1:j2] + x[i2 + p:]
                                elif i1 == 0 and i2 + p == sp:
                                    x = f1_text[d][j1:j2]
                                elif i1 > 0 and i2 + p < sp:
                                    x = x[:i1 + p] + f1_text[d][j1:j2]\
                                        + x[i2 + p:]
                                elif i1 > 0 and i2 + p == sp:
                                    x = x[:i1 + p] + f1_text[d][j1:j2]
                            if len(matcher.a[i1:i2]) > len(matcher.b[j1:j2]):
                                p -= len(matcher.a[i1:i2]) - \
                                     len(matcher.b[j1:j2])
                            if len(matcher.a[i1:i2]) < len(matcher.b[j1:j2]):
                                p += len(matcher.b[j1:j2]) - \
                                     len(matcher.a[i1:i2])
                else:
                    x = i

                ls.append(x)

    with open(ss, "w") as fc:
        for d in ls:
            fc.write("%s\n" % d)

    with open(ss) as f_input:
        data = f_input.read().rstrip('\n')

    with open(ss, 'w') as f_output:
        f_output.write(data)


def getsize(filename):
    st = os.stat(filename)
    return st.st_size


def compare_different(comp, s, ss, arg):
    if comp.diff_files:
        for i in comp.diff_files:
            f = os.path.join(s, i)
            d = os.path.join(ss, i)
            if os.access(f, os.R_OK):
                if arg.update and getmtime(f) <= getmtime(d):
                    pass
                elif arg.checksum:
                    if checksum(f) != checksum(d):
                        modify_file(f, d)
                        run_arguments(f, d, arg)

                else:
                    modify_file(f, d)
                    run_arguments(f, d, arg)
            else:
                pt = os.path.join(os.getcwd(), arg.source)
                file_error1(pt)
                file_error_sub()


def sym_link(s, ss):
    lnk = os.readlink(s)
    if os.path.exists(ss):
        os.remove(ss)
    os.symlink(lnk, ss)


def compare_left(comp, s, ss, arg):
    pt = os.path.join(os.getcwd(), arg.source)
    if comp.left_only:
        for i in comp.left_only:
            if os.path.isfile(os.path.join(s, i)):
                f = os.path.join(s, i)
                d = os.path.join(ss)
                if os.access(f, os.R_OK):
                    if os.access(f, os.R_OK):
                        if not check_index(d):
                            if os.path.islink(f):
                                sym_link(f, d)
                            elif check_innode(f):
                                os.link(f, d)
                            else:

                                try:
                                    shutil.copy2(f, d)
                                except EnvironmentError as e:
                                    print(e)
                        else:
                            file_error_sub2(os.getcwd(), d)
                            error_io()
                else:
                    file_error1(pt)
                    file_error_sub()
            if os.path.isdir(os.path.join(s, i)):
                fx = os.path.join(s, i)
                dx = os.path.join(ss, i)
                if os.access(fx, os.R_OK):
                    copy_directory(fx, dx)
                else:
                    dir_error1(pt)
                    file_error_sub()


def compare_differentx(comp, s, ss):
    if comp.diff_files:
        for i in comp.diff_files:
            f = os.path.join(s, i)
            d = os.path.join(ss, i)
            if os.access(f, os.R_OK):
                if "-u" or "--update" in sys.argv and getmtime(f) <= getmtime(d):
                    pass
                elif "-c" or "--checksum" in sys.argv:
                    if checksum(f) != checksum(d):
                        modify_file(f, d)
                        run_argumentsx(f, d)

                else:
                    modify_file(f, d)
                    run_argumentsx(f, d)
            else:
                pt = os.path.join(os.getcwd(), s)
                file_error1(pt)
                file_error_sub()


def compare_leftx(comp, s, ss, arg):
    pt = os.path.join(os.getcwd(), arg)
    if comp.left_only:
        for i in comp.left_only:
            if os.path.isfile(os.path.join(s, i)):
                f = os.path.join(s, i)
                d = os.path.join(ss, i)
                if os.access(f, os.R_OK):
                    if os.access(f, os.R_OK):
                        if not check_index(d):
                            if os.path.islink(f):
                                sym_link(f, d)
                            elif check_innode(f):
                                os.link(f, d)
                            else:
                                try:
                                    shutil.copy2(f, d)
                                except EnvironmentError:
                                    print("Invalid action")
                        else:
                            file_error_sub2(os.getcwd(), d)
                            error_io()
                else:
                    file_error1(pt)
                    file_error_sub()
            if os.path.isdir(os.path.join(s, i)):
                fx = os.path.join(s, i)
                dx = os.path.join(ss, i)
                if os.access(fx, os.R_OK):
                    copy_directory(fx, dx)
                else:
                    dir_error1(pt)
                    file_error_sub()


def check_options(arg, s, d):
    if arg.update and os.path.getmtime(s) <= os.path.getmtime(d):
        return False
    elif arg.checksum and checksum(s) == checksum(d):
            return False
    elif getsize(s) == getsize(d) and \
            os.path.getmtime(s) == os.path.getmtime(d):
        return False
    return True


def check_arguments(arg):
    # if source is directory and destination is a file
    s = os.path.normpath(arg.source)
    d = os.path.normpath(arg.destination)
    if os.path.isdir(s) and os.path.isfile(d):
        directory_error()
        error_io1()

    # if source is file and destination is a file
    elif os.path.isfile(s) and \
            os.path.isfile(d):
        if not os.access(d, os.W_OK):
            os.chmod(d, 0o777)

        if os.access(s, os.R_OK):
            if check_options(arg, s, d):
                modify_file(s, d)
                run_arguments(s, d, arg)
        else:
            pt = os.path.join(os.getcwd(), arg.source)
            file_error1(pt)
            file_error_sub()

    # if source is file and destination is a directory
    elif os.path.isfile(s) and os.path.isdir(d):
        if os.access(s, os.R_OK):
            pt = os.path.join(os.getcwd(), arg.source)
            file_name = os.path.basename(arg.source)
            ss = os.path.join(d, file_name)
            if os.path.exists(ss):
                if os.access(ss, os.W_OK):
                    if check_options(arg, s, ss):
                        modify_file(s, ss)
                        run_arguments(s, ss, arg)
                else:
                    write_error(pt)
                    file_error_sub()

            else:
                if os.access(d, os.W_OK):
                    if not check_index(ss):
                        if os.path.islink(s):
                            sym_link(s, ss)

                        elif check_innode(s):
                            os.link(s, ss)
                        else:
                            try:
                                shutil.copy2(s, ss)

                            except EnvironmentError:
                                print("Invalid action")

                    else:
                        file_error_sub2(os.getcwd(), d)
                        error_io()
                else:
                    pt = os.path.join(os.getcwd(), d)

                    write_error(pt)
                    file_error_sub()

        else:
            pt = os.path.join(os.getcwd(), arg.source)
            file_error1(pt)
            file_error_sub()

    # if source is directory and destination is a directory and non recursive
    elif os.path.isdir(s) and os.path.isdir(d) and not arg.recursive:
        print('Skipping directory'+" "+arg.source)

    # if source is directory and destination is a directory and recursive
    elif os.path.isdir(s) and os.path.isdir(d) and arg.recursive:
        if os.access(s, os.R_OK):

            if '/' not in arg.source:
                if os.path.exists(os.path.join(d, arg.source)):
                    ss = os.path.join(d, arg.source)
                    comparison = filecmp.dircmp(s, ss)
                    compare_different(comparison, s, ss, arg)
                    compare_left(comparison, s, ss, arg)

                    if not is_same(s, ss):

                            recursive_search(os.path.join(s), os.path.join(d,
                                             arg.source), arg)

                else:
                    copy_directory(os.path.join(s), os.path.join(d, arg.source))

            if '/' in arg.source:
                f = str(arg.source)
                fx = (f[len(f)-1:])

                if '/' not in fx:

                    pathsub = os.path.basename(os.path.join(d, arg.source))
                    if os.path.exists(os.path.join(d, pathsub)):
                        s = os.path.join(d)
                        ss = os.path.join(d, pathsub)
                        comparison = filecmp.dircmp(s, ss)
                        compare_different(comparison, s, ss, arg)
                        compare_left(comparison, s, ss, arg)

                        if not is_same(s, (os.path.join(d, pathsub))):
                            recursive_search(os.path.join(s),
                                             (os.path.join(d, pathsub)),
                                             arg)

                    else:
                        if os.access(fx, os.R_OK):
                            sx = os.path.join(s)
                            copy_directory(sx, os.path.join(d, pathsub))

                        else:
                            pt = os.path.join(os.getcwd(), arg.source)
                            dir_error1(pt)
                            file_error_sub()

                else:

                    s = os.path.join(s)
                    ss = os.path.join(d)

                    comparison = filecmp.dircmp(s, ss)
                    compare_different(comparison, s, ss, arg)
                    compare_left(comparison, s, ss, arg)
                    if not is_same(os.path.join(s),
                                   os.path.join(d)):
                        recursive_search(os.path.join(s),
                                         (os.path.join(d)), arg)
        else:
            pt = os.path.join(os.getcwd(), arg.source)
            dir_error1(pt)
            file_error_sub()


def check_file_validity(arg):
    src = os.path.join(arg.source)
    dst = os.path.join(arg.destination)
    if os.path.isdir(os.path.normpath(arg.source)):
        dc = os.path.normpath(arg.source)
        if os.access(dc, os.R_OK):
            if '/' in arg.source:
                if not check_index(arg.source):
                    d = os.path.join(arg.destination,
                                     os.path.basename(arg.source))
                    copy_directory(src, d)
                else:
                    copy_directory(src, dst)

        else:
            pt = os.path.join(os.getcwd(), arg.source)
            dir_error1(pt)
            file_error_sub()
    else:
        if not check_index(dst):
            if os.access(os.path.join(arg.source), os.R_OK):
                if os.path.islink(src):
                    sym_link(src, dst)

                elif check_innode(src):
                    os.link(src, dst)
                else:
                    shutil.copy2(src, dst)

            else:
                pt = os.path.join(os.getcwd(), arg.source)
                file_error1(pt)
                file_error_sub()
        else:
            file_error_sub2(os.getcwd(), dst)
            error_io()


def is_valid_file(par, arg):
    # check if the file is a valid path

    try:
        if not (os.path.exists(arg.source)):
            file_error2(os.getcwd(), arg.source)
        else:
            if os.path.exists(arg.destination):
                # check for positional arguments
                check_arguments(arg)
            else:
                # destination file/ directory has children
                if "/" in arg.destination:
                    s = arg.destination
                    ls = (s.split('/'))
                    x = os.path.join(os.path.normpath(ls[0]))
                    pt = os.path.join(os.getcwd(), arg.destination)
                    if os.path.exists(x):
                        for d, i in enumerate(ls):
                            if d > 0:
                                if os.path.exists(os.path.join(x, i)):
                                    x = os.path.join(x, i)
                                else:
                                    if d+1 == len(ls):
                                        check_file_validity(arg)
                                        break

                                    else:

                                        dir_error2(pt)
                                        file_error_sub1()
                                        break

                    else:
                        s = arg.source
                        d = arg.destination
                        if check_index(d):
                            if not os.path.exists(d):
                                if os.path.isfile(s):
                                    os.mkdir(d)
                                    shutil.copy2(s, d)
                                if os.path.isdir(s):
                                    try:
                                        shutil.copytree(s, d, True)

                                    except OSError:
                                        file_error_sub()
                        else:
                            dir_error2(pt)
                            file_error_sub1()
                else:
                    # if the destination file/ directory has no children
                    pt = os.getcwd()
                    file_name = os.path.basename(arg.source)
                    file_dir = os.path.dirname(arg.source)
                    if os.path.isdir(os.path.normpath(arg.source)):
                        if os.access(os.path.normpath(arg.source), os.R_OK):
                            sx = os.path.join(arg.source)
                            if '/' in arg.source:
                                if check_index(arg.source):
                                    ptx = os.path.join(pt, arg.destination)
                                    copy_directory(sx, ptx)
                                else:
                                    pt1 = os.path.join(pt, arg.destination)
                                    ptx = os.path.join(pt1, file_name)
                                    copy_directory(sx, ptx)

                            else:
                                pt1 = os.path.join(pt, arg.destination)
                                ptx = os.path.join(pt1, file_name)
                                copy_directory(sx, ptx)

                        else:
                            pt = os.path.join(os.getcwd(), arg.source)
                            dir_error1(pt)
                            file_error_sub()

                    else:
                        pt = os.path.join(os.getcwd())
                        d = os.path.join(pt, arg.destination)
                        sc = os.path.join(file_dir, file_name)
                        if os.access(sc, os.R_OK):
                            if not check_index(d):
                                if os.path.islink(sc):
                                    sym_link(sc, d)

                                elif check_innode(sc):
                                    os.link(sc, d)

                                else:
                                    shutil.copy2(sc, d)
                            else:
                                file_error_sub2(os.getcwd(), d)
                                error_io()

                        else:
                            file_error1(pt)
                            file_error_sub()

    except TypeError:
        print("Invalid file path")


def msg():
    return "usage: rsync.py [-h] [-p] [-r] [-o] " \
           "[-g] [-t] [-I] [-H] [-u] [-c] " \
           "source file, destination file"


def file_error2(pwd, a):
    print("rsync: link_stat " + '"' + pwd + "/" + a + '"'
          + " " + "failed: No such file or directory (2)")


def is_file_or_directory():
    k = 0
    for i in range(len(sys.argv) - 2):
        if os.path.exists(sys.argv[i + 1]):
            if os.path.isfile(sys.argv[i + 1]):
                if k == 0:
                    k = k+1
                elif k > 0:
                    return True

            if os.path.isdir(sys.argv[i + 1]):
                return True
    return False


def main():
    # Configure the option parser
    parser = argparse.ArgumentParser(description='rsync')
    parser.add_argument("source", help="Source directory/file to be copied")
    parser.add_argument("destination", help="Destination directory/file")
    parser.add_argument("-p", "--permission", action="store_true",
                        dest="permission", default=True,
                        help="transfer permission")
    parser.add_argument("-r", "--recursive", action="store_true",
                        dest="recursive", default=False,
                        help="recursive")
    parser.add_argument("-o", "--owner", action="store_true",
                        dest="owner", default=True,
                        help="preserve owner (super-user only)")
    parser.add_argument("-g", "--group", action="store_true",
                        dest="group", default=True,
                        help="preserve group")
    parser.add_argument("-t", "--times", action="store_true",
                        dest="times", default=True,
                        help="preserve modification times")
    parser.add_argument("-I", "--links", action="store_true",
                        dest="links", default=True,
                        help="preserve symlinks")
    parser.add_argument("-H", "--hard-links", action="store_true",
                        dest="hardlinks", default=True,
                        help="preserve hardlinks")
    parser.add_argument("-u", "--update", action="store_true",
                        dest="update", default=False,
                        help="skip files that are newer on the receiver")
    parser.add_argument("-c", "--checksum", action="store_true",
                        dest="checksum", default=False,
                        help="skip based on checksum, not mod-time & size")

    try:
        g = io.StringIO()
        with redirect_stderr(g):
            args = parser.parse_args()
            if args.destination:
                # check if the file is valid
                is_valid_file(parser, args)
    except SystemExit:
        if sys.argv[0] == "rsync.py":
            if len(sys.argv) == 2 and "-" not in sys.argv[1]:
                file_error2(os.getcwd(), sys.argv[1])
                file_error_sub()

            elif len(sys.argv) == 3 and "-" not in sys.argv[1] \
                    and "-" not in sys.argv[2]:
                if '/' in sys.argv[1] and '/' not in sys.argv[2]:
                    if not check_index(sys.argv[1]):
                        file_error2(os.getcwd(), sys.argv[1])
                        file_error_sub()

                    else:
                        file_error3(os.getcwd(), sys.argv[1])
                        file_error_sub()

                elif '/' in sys.argv[1] and '/' in sys.argv[2]:
                    if check_index(sys.argv[1]) and check_index(sys.argv[2]):
                        pt = os.path.join(os.getcwd(), sys.argv[2])
                        if os.path.exists(pt):
                            file_error3(os.getcwd(), sys.argv[1])
                            file_error_sub()
                        else:
                            file_error3(os.getcwd(), sys.argv[1])
                            file_error_sub2(os.getcwd(), sys.argv[1])
                            error_io()

                else:
                    file_error2(os.getcwd(), sys.argv[1])
                    file_error_sub()

            elif len(sys.argv) == 3 and "-" in sys.argv[1] \
                    and "-" not in sys.argv[2]:
                pt = os.path.join(os.getcwd(), sys.argv[2])
                if os.path.exists(pt):
                    print(sys.argv[2])
                    print(os.stat(os.path.exists(pt)))
                else:
                    file_error2(os.getcwd(), sys.argv[2])
                    file_error_sub()

            elif len(sys.argv) == 3 and "-" not in sys.argv[1] and "-" in \
                    sys.argv[2]:
                pt = os.path.join(os.getcwd(), sys.argv[1])
                if os.path.exists(pt):
                    print(sys.argv[1])
                    print(os.stat(os.path.exists(pt)))

                else:
                    file_error2(os.getcwd(), sys.argv[1])
                    file_error_sub()

            elif len(sys.argv) > 3:
                ln = len(sys.argv)
                for i in range(len(sys.argv)-2):
                    if not os.path.exists(sys.argv[i+1]):
                        file_error2(os.getcwd(), sys.argv[i+1])
                    else:
                        dst = sys.argv[ln - 1]
                        src = sys.argv[i+1]
                        # destination doesn't exist
                        if not os.path.exists(dst):
                            if os.path.isfile(src):
                                if is_file_or_directory():
                                    os.mkdir(dst)
                                shutil.copy2(src, dst)
                            elif os.path.isdir(src):
                                if os.path.isdir(src):
                                    bs = os.path.basename(src)

                                    if check_index(src):
                                        shutil.copytree(src, dst
                                                        , True)

                                    else:
                                        shutil.copytree(src,
                                                        os.path.join(dst, bs),
                                                        True)

                        else:
                            if os.path.isfile(dst):
                                directory_error()
                                error_io1()
                                break

                            if os.path.isdir(dst):
                                sc = os.path.join(dst, src)
                                if os.path.exists(sc):
                                    if os.path.isfile(src):
                                        modify_file(src, sc)
                                    elif os.path.isdir(src):
                                        if check_index(src):

                                            comparison = filecmp.dircmp(src,
                                                                        dst)

                                            compare_leftx(comparison, src, dst,
                                                          src)
                                            compare_differentx(comparison,
                                                               src, dst)
                                            if not is_same(src, dst):
                                                recursive_searchx(
                                                    os.path.join(src),
                                                    os.path.join(dst), src)

                                        else:
                                            comparison = filecmp.dircmp(src,
                                                                        sc)

                                            compare_leftx(comparison, src, sc,
                                                          src)
                                            compare_differentx(comparison,
                                                               src, sc)

                                            if not is_same(src, sc):
                                                recursive_searchx(
                                                    os.path.join(src),
                                                    os.path.join(sc), src)

                                else:
                                    bs = os.path.basename(src)
                                    if os.path.isfile(src):
                                        shutil.copy2(src, dst)
                                    elif os.path.isdir(src):
                                        if check_index(src):
                                            comparison = filecmp.dircmp(src,
                                                                        dst)

                                            compare_leftx(comparison, src, dst,
                                                          src)
                                            compare_differentx(comparison,
                                                               src, dst)
                                            if not is_same(src, dst):
                                                recursive_searchx(
                                                    os.path.join(src),
                                                    os.path.join(dst), src)

                                        else:

                                            shutil.copytree(src,
                                                            os.path.join(dst,
                                                                         bs),
                                                            True)

            elif len(sys.argv) == 1 or len(sys.argv) == 2 \
                    and "-" in sys.argv[1]:
                print(msg())

        exit(2)


if __name__ == '__main__':
    main()
