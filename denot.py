import os
import re
import sys
from pathlib import Path
from getopt import getopt, GetoptError
from subtitle_block import SubtitleBlock


class Regex(object):
    INDEX = r'^[0-9]+$'
    TIMEFRAME = r'^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} *--> *[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$'
    NAME = r'^(.*?: ?).*$'
    MUSIC = r'^.*?(?:â™ª)+.*?$'
    AUTHOR = r'^.*?subtitle(?:s|d) by.*?$'
    SYNC = r'^.*?sync(?:ed)? by.*?$'
    FONT_COLOR_START = r'<font color=".*?">'
    FONT_COLOR_END = r'</font>'
    LINES = [
        r'^(?:- |.*?: *)?\(?.*?\)(.*)?$',
        r'^(?:- |.*?: *)?\(.*?\)?(.*)?$',
        r'^(?:- |.*?: *)?\[?.*?\](.*)?$',
        r'^(?:- |.*?: *)?\[.*?\]?(.*)?$',
        MUSIC
    ]


def usage(exit_code=0):
    print(f'{os.path.basename(__file__)} [-h] [-f <file>] [-d <directory>] [-p <path>] [-q]')

    if exit_code is not None:
        sys.exit(exit_code)


def is_allowed_file_extension(file, allowed_extensions=('srt',)):
    return any([file.endswith(ext) for ext in allowed_extensions])


def scan_directory(directory):
    if not isinstance(directory, Path):
        directory = Path(directory)
    return [x for x in directory.iterdir() if x.is_file()]


def validate_file(file, cwd=True, v_ext=True):
    path = file if isinstance(file, Path) else Path(file)
    if not is_allowed_file_extension(path.suffix):
        if v_ext:
            print(f'Invalid file extension "{path.suffix}"')
        return None
    if cwd:
        path = Path.cwd() / file
    if not path.exists():
        print(f'File does not exist "{path}"')
        return None
    return path


def validate_directory(directory):
    path = directory if isinstance(directory, Path) else Path(directory)
    if not path.exists():
        print(f'Directory does not exist "{path}"')
        return None
    files = scan_directory(path)
    v_files = []
    for file in files:
        v_file = validate_file(file, cwd=False, v_ext=False)
        if v_file:
            v_files.append(v_file)
    return v_files if v_files else None


def parse_line(line):
    return line.strip().replace('ï»¿', '')


def write_block_to_file(block, file):
    if not block.is_valid():
        return False
    path = file if isinstance(file, Path) else Path(file)
    with path.open(mode='a' if block.index > 1 else 'w') as out_file:
        out_file.write(str(block))
    return True


def process_file(file):
    path = file if isinstance(file, Path) else Path(file)
    contents = path.read_text()
    if not contents:
        return 0

    print_first_n_lines = 0
    print_count = 0
    total_removed = 0
    current_block = None
    next_block_index = 1
    skip_next_line = False
    lines = contents.split('\n')
    for line in lines:
        s_line = parse_line(line)

        if print_count < print_first_n_lines:
            print_count += 1
            print(f'[{print_count:02d}] {s_line}')

        if not s_line:
            skip_next_line = False
            continue

        if re.match(Regex.INDEX, s_line, re.I):
            if current_block:
                if write_block_to_file(current_block, path):
                    next_block_index += 1
            current_block = SubtitleBlock(index=next_block_index)
        elif re.match(Regex.TIMEFRAME, s_line, re.I):
            if not current_block:
                continue
            current_block.timeframe = s_line
        else:
            if not current_block:
                continue

            if skip_next_line:
                skip_next_line = False
                total_removed += 1
                continue

            tmp_line = s_line
            s_line = re.sub(Regex.FONT_COLOR_START, '', s_line, re.I)
            s_line = re.sub(Regex.FONT_COLOR_END, '', s_line, re.I)
            if s_line != tmp_line:
                total_removed += 1

            if re.match(Regex.AUTHOR, s_line, re.I) or re.match(Regex.SYNC, s_line, re.I):
                skip_next_line = True
                total_removed += 1
                continue

            match_obj = re.match(Regex.NAME, s_line, re.I)
            if match_obj:
                s_line = s_line.replace(match_obj.group(1), '').strip()
                total_removed += 1

            if not s_line:
                continue

            skip = False
            for regex in Regex.LINES:
                match_obj = re.match(regex, s_line, re.I)
                if match_obj:
                    if len(match_obj.groups()) > 0:
                        s_line = match_obj.group(1)
                    else:
                        skip = True
                    total_removed += 1
                    break

            if not skip:
                current_block.add_line(s_line)

    if current_block:
        write_block_to_file(current_block, path)

    return total_removed


def main(argv):
    try:
        short_opts = 'hf:d:p:q'
        long_opts = ['help', 'file=', 'directory=', 'path=', 'quiet']
        opts, args = getopt(argv, short_opts, long_opts)
    except GetoptError:
        usage(2)

    quiet_flag = False
    files_to_process = []
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-f', '--file'):
            ret = validate_file(arg)
            if ret:
                files_to_process.append(ret)
        elif opt in ('-d', '--directory'):
            ret = validate_directory(arg)
            if ret:
                files_to_process.extend(ret)
        elif opt in ('-p', '--path'):
            if Path(arg).is_file():
                ret = validate_file(arg)
                if ret:
                    files_to_process.append(ret)
            else:
                ret = validate_directory(arg)
                if ret:
                    files_to_process.extend(ret)
        elif opt in ('-q', '--quiet'):
            quiet_flag = True

    if not files_to_process:
        ret = validate_directory(Path.cwd())
        if ret:
            files_to_process.extend(ret)

    if not files_to_process:
        print('No subtitle files found to process')
        return

    file_count = len(files_to_process)
    s = '' if file_count == 1 else 's'

    if not quiet_flag:
        input_prompt = f'{file_count} subtitle file{s} found. Proceed? [Y/n] '
        i = input(input_prompt)
        while i and str(i).strip().lower() not in ('y', 'n'):
            i = input(input_prompt)
        if i and str(i).strip().lower() == 'n':
            return

    deleted_count = sum([process_file(file) for file in files_to_process])
    print(f'Removed {deleted_count} annotations in {file_count} file{s}.')


if __name__ == '__main__':
    main(sys.argv[1:])
