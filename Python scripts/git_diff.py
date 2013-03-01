import os
import subprocess
import re
import time
import sys
import shutil
import fnmatch
import logging as log
import argparse
import datetime
import calendar
import chardet
from prettydiff import poot

from config import config


today = datetime.date.today()

parser = argparse.ArgumentParser(
    description="Generate patch diff for Valve games")

parser.add_argument("game",
                    help="the game to generate a patch diff for, corresponds to a config entry")

parser.add_argument("day",
                    type=int,
                    nargs="?",
                    default=today.day,
                    help="the calendar day of the patch, default: today")

parser.add_argument("month",
                    type=int,
                    nargs="?",
                    default=today.month,
                    help="the calendar month of the patch, default: current month")

parser.add_argument("year",
                    type=int,
                    nargs="?",
                    default=today.year,
                    help="the calendar month of the patch, default: current month")

parser.add_argument("-v",
                    "--verbose",
                    dest="verbose",
                    action="store_true",
                    help="be verbose about what we are doing")

parser.add_argument("-n",
                    "--patch-number",
                    type=int,
                    dest="patch_number",
                    action="store",
                    help="the patch number of the day, e.g: 2")

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(0)

args = parser.parse_args()
patch = "%s %02d, %d Patch" % (
                                calendar.month_name[args.month],
                                args.day,
                                args.year)

if args.patch_number:
    patch = "%s %d" % (patch, args.patch_number)
print patch
sys.exit()

log.basicConfig(
    stream=sys.stderr,
    format="%(levelname)s: %(message)s",
    level=log.DEBUG)


def compare(sourceDir, targetDir, ignorePattern):
    """Compare two directories and return list of missing files\
    from the target directory"""
    missing = []

    # verify existence of source directory
    if not os.path.exists(sourceDir):
        log.critical("sourceDir doesn't exist: %s" % sourceDir)
        sys.exit(1)

    if not os.path.isdir(sourceDir):
        log.critical("sourceDir not a directory: %s" % sourceDir)
        sys.exit(1)

    # verify existence of target directory
    if not os.path.exists(targetDir):
        log.critical("targetDir doesn't exist: %s" % targetDir)
        sys.exit(1)

    if not os.path.isdir(targetDir):
        log.critical("targetDir not a directory: %s" % targetDir)
        sys.exit(1)

    regexp = re.compile(ignorePattern, re.IGNORECASE)
    # walk the sourceDirectory...
    for root, dirs, files in os.walk(sourceDir):

        subDir = root.replace(sourceDir, '')
        targetSubDir = os.path.join(targetDir, subDir)

        # skip files if they match our ignore pattern
        result = regexp.search(targetSubDir)
        if result:
            continue

        # check to see if targetSubDir exists
        if not os.path.exists(targetSubDir) or not os.path.isdir(targetSubDir):
            log.warning("sourceDir %s not found at %s" % (root, targetSubDir))
            missing.append(os.path.normpath(root))
            continue

        # verify that each file in root exists in targetSubDir
        for sourceFile in files:
            # skip symbolic links
            if os.path.islink(os.path.join(root, sourceFile)):
                continue

            targetFile = os.path.join(targetSubDir, sourceFile)
            if not os.path.exists(targetFile):
                log.debug("%s in %s is missing from %s" % (sourceFile, root, targetSubDir))
                missing.append(os.path.join(os.path.normpath(root), sourceFile))

            if os.path.exists(targetFile) and not os.path.isfile(targetFile):
                log.debug("%s in %s is not a valid file in %s" % (sourceFile, root, targetSubDir))

    return missing


def moveDirectory(root_src_dir, root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for f in files:
            src_file = os.path.join(src_dir, f)
            dst_file = os.path.join(dst_dir, f)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)


def get_encoding(string):
    """Returns character encoding"""
    encoding = chardet.detect(string)
    return encoding['encoding']

def txt_to_utf8(dir):
    """Walks a directory tree and converts any txt files to UTF-8 encoding"""
    for root, dirs, files in os.walk(dir):
        for f in files:
            if f.endswith(".txt"):
                try:
                    fullpath = os.path.join(root, f)
                    filecontents = open(fullpath, 'rb').read()
                    encoding = get_encoding(filecontents)
                    utf8string = unicode(filecontents, encoding).encode("utf-8")
                    open(fullpath, 'wb').write(utf8string)
                except Exception, e:
                    log.warning("%s: %s" % (f, e))

def main():
    choice = None

    # Check to see which game has been specified via the launch arguments.
    if len(sys.argv) < 2:
        print "Please specify the game to diff"
        choices = []
        for game in config:
            if game != "fallback":
                choices.append(game)
        choice = get_choice(choices)

    # Try load config for specified game.
    try:
        fallback = config["fallback"]
        if choice is not None:
            working = config[choice]
        else:
            working = config[sys.argv[1]]

        workingRepoDir = working.get("workingRepoDir", fallback["workingRepoDir"])
        tempDir = working.get("tempDir", fallback["tempDir"])
        gameFolder = working.get("gameFolder", fallback["gameFolder"])
        diffOutput = working.get("diffOutput", fallback["diffOutput"])
        patchNameFormat = working.get("patchNameFormat", fallback["patchNameFormat"])
        wikiApi = working.get("wikiApi", fallback["wikiApi"])
        wikiUsername = working.get("wikiUsername", fallback["wikiUsername"])
        wikiPassword = working.get("wikiPassword", fallback["wikiPassword"])
        hlExtract = working.get("hlExtract", fallback["hlExtract"])
        name = os.path.split(gameFolder)[1]

    except:
        print 'Error: First argument must be a supported game:'
        sys.exit(1)

    # Get patch title - get all user input before doing work.
    patchTitle = getPatchName(patchNameFormat)

    auto_wiki = raw_input("Submit diff to wiki upon completion?").lower() != "n"
    start_time = time.mktime(time.gmtime())

    # Create temp directory
    if not os.path.isdir(tempDir):
        os.mkdir(tempDir)
    else:
        print "Johnny: \tCAPTAIN, WE HAVE REMNANTS OF AN OLD TEMPDIR!"
        print "Captain: \tARRR, THAT AINT IDEAL.  KABLEWM THE SCALLYWAGS OUTA THE OCEAN I SAY!"
        print "Johnny: \tMENTLEMENS, LASER THE BEEMZ!"
        shutil.rmtree(tempDir)
        print "Sniper: \t Thanks for standin still, ganker!"
        os.mkdir(tempDir)

    # Copy files to temp dir.
    print "Copying files to temp directory"
    copyToTempdir = r'xcopy "{source!s}" "{destination!s}" /E /Q'.format(source=gameFolder, destination=tempDir)
    returnCopyToTempdir = subprocess.call(copyToTempdir, shell=True)
    if returnCopyToTempdir != 0:
        shutil.rmtree(tempDir)
        print 'Error: Shutdown the Steam client first dummkopf'
        sys.exit(1)

    # Extract VPKs
    vpks = []
    for root, dirs, files in os.walk(tempDir):
        for f in files:
            if fnmatch.fnmatch(f, "*.vpk"):
                vpks.append(root + os.sep + f)

    vpk_dirs = []
    for root, dirs, files in os.walk(tempDir):
        for f in files:
            if fnmatch.fnmatch(f, "*_dir.vpk"):
                vpk_dirs.append(root + os.sep + f)

    for vpk in vpk_dirs:
        print "Extracting vpk: {}".format(vpk)

        command = "{hle} -s -p {vpk} -d {dest} -e root".format(hle=hlExtract, vpk=vpk, dest=tempDir)
        return_code = subprocess.call(command)
        assert return_code == 0

        os.remove(vpk)
        shutil.copytree(tempDir + os.sep + "root", vpk)
        shutil.rmtree(tempDir + os.sep + "root")

    for vpk in vpks:
        if os.path.isfile(vpk):
            os.remove(vpk)

    #Find deleted files, remove them from svn
    missingfiles = compare(workingRepoDir + os.sep + name, tempDir,  r'\.git')
    if len(missingfiles) != 0:
        print "\nFiles removed from files:"
        for f in missingfiles:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                elif os.path.isfile(f):
                    os.remove(f)
    else:
        print "\nNo files removed from files."

    # Convert .txt files to utf-8
    print "\nConverting relevant files to utf-8 and decrypting ctx files"
    txt_to_utf8(tempDir)

    # Moving files to working repository.
    print "\nMoving files to working repository"
    moveDirectory(tempDir, workingRepoDir + os.sep + name)

    # Delete temp directories
    print "\nDeleting temporary directory."
    shutil.rmtree(tempDir)

    commit_message = patchTitle
    # Stage all changes to git repo
    print '\nStaging changes in git repo'
    subprocess.Popen(['git', 'add', '-A'], shell=True, cwd=workingRepoDir).communicate()

    # Commit to wiki
    if not auto_wiki:
        raw_input("Ready to submit to Wiki.  Hit enter to go ahead.")
    print "\nSubmitting prettydiff to wiki"
    poot(wikiApi, wikiUsername, wikiPassword, patchTitle, workingRepoDir)

    # Get git .diff
    print '\nGenerating git diff file'
    outputfile = open(diffOutput, 'wb')
    subprocess.Popen(['git', 'diff', '-U', '--cached'], shell=True, stdout=outputfile, cwd=workingRepoDir).communicate()

    # Commit to repo
    print '\nCommiting to repo'

    commit_message1 = patchTitle
    commit_message = ['-m', commit_message1]

    subprocess.Popen(['git', 'commit'] + commit_message, shell=True, cwd=workingRepoDir).communicate()
    print "Finished. Time taken: {} seconds".format(time.mktime(time.gmtime()) - start_time)
if __name__ == "__main__":
    pass
    #main()
