import time

config = {"fallback": {"workingRepoDir": r'',  # Directory where Git repo exists
                       "tempDir": r'',  # Directory where files will be temporarily stored. (lots of writing/reading)
                       "hlExtract": r'R:\Diffs\tools\hlextract\HLExtract.exe',  # Where HLExtract.exe resides
                       "gameFolder": r'',  # The in which the game resides
                       "diffOutput": r'',  # Location and name of file for raw svn diff output
                       "patchNameFormat": r"%B %d, %Y Patch",
                       "wikiApi": r"http://www.dota2wiki.com/api.php",
                       "wikiUsername": r"RBotson",
                       "wikiPassword": r""
                      },
         "dota2beta": {"workingRepoDir": r'R:\Diffs\git\dota2beta',
                       "tempDir": r'R:\Diffs\raw_files\dota2beta',
                       "gameFolder": r'R:\Diffs\raw_steam\steamapps\common\dota 2 beta',
                       "diffOutput": r'R:\Diffs\raw_diffs\dota2beta_{generate_time!s}.txt'.format(generate_time = time.mktime(time.gmtime())),
                       "patchNameFormat": r"%B %d, %Y Patch"
                       },
         "dota2test": {"workingRepoDir": r'R:\Diffs\git\dota2test',
                       "tempDir": r'R:\Diffs\raw_files\dota2test',
                       "gameFolder": r'R:\Diffs\raw_steam\steamapps\common\dota 2 test',
                       "diffOutput": r'R:\Diffs\raw_diffs\dota2test_{generate_time!s}.txt'.format(generate_time = time.mktime(time.gmtime())),
                       "patchNameFormat": r"%B %d, %Y Patch (Test)"
                       }
        }
