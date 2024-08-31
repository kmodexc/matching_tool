## Run code

Because of module imports its not possible to run the python files directly (exept `run.py`). To run files for development use the following:

```
cd src
python run.py                             # start the application
python -m tufast_matching_tool.testpd     # run a specific file in the module
```

## Create executable

If you want to create the executable you just execute this command from the workspace dir:

```
pyinstaller --onefile --windowed --add-data "tufast_img.ico:." --icon "tufast_img.ico" --name tufast_matching_tool src/run.py
```

However to create if for multiple platforms you need to create a github account create a tag (that matches the version in `pyproject.toml`) and then push everything to github. Then github will automatically build the executables for all platforms (windows, linux, mac). The executables can be downloaded after some minutes under releases in the assets.

First create a new origin for your github repo.

```
git remote add origin-gh git@github.com:<your-user>/matching_tool.git
```

Then every time for a new version do

```
git commit -a               # commit changes (if not already done)
git push --all              # push everything to the tufast gitlab
git push --all origin-gh    # push everything to github
git tag <version-name>      # create a tag with the version string i.e. v1.2.3
                            # make shure the version is the same as in pyproject.toml
                            # and just add a 'v' before that.
git push --tags origin-gh   # push all tags to github
```

