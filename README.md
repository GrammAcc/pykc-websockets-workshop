# Python Kansas City Summer 2024 Workshop

## Realtime Web Applications with WebSockets -- @GrammAcc

This is the workshop project accompanying the lecture I gave at the Python KC summer meetup.

This workshop is being facilitated remotely over the PyKC discord, so if you didn't make it to the lecture, you can still participate.
You will need to reach out to one of the Python KC organizers for an invite if you are not already a member of the discord.

There is a workshops channel in the discord where I will be available to answer questions and provide guidance whenever I can. The project should be fairly straightforward though, so I expect that most questions will be some form of *why* as opposed to *how*.

### Getting Started

Everything about this project is automated, so it should be easy to get up and running.

After cloning the repo, navigate to the project root directory and run `python genenv.py`.

This script will create a `.env` file and a `server.toml` file with some needed values in the root directory.
This is necessary because the `.env` file contains secret keys used in the application's
cryptographic security, so it can't be checked into source control, and the `server.toml` file
contains SSL configuration for hypercorn, which is only needed if you enable [Local HTTPS](#local-https), so having it
available for users that want to set that up is useful, but it needs to be generated with comments to
avoid breaking default behavior.

The `genenv.py` script creates random keys for the needed secrets and also sets the
LOG_LEVEL and SITE_ROOT env vars which are used to make the application easier
to refactor.

#### Getting Hatch

This project is managed with [hatch](https://hatch.pypa.io/latest/), so you
will need to install hatch if you don't have it already.

You can install hatch globally or into a virtual environment.

The easiest way to install hatch is with the `gethatch` script provided
in this repo. On Unix systems, simply run `source gethatch.sh`, or on Windows,
you can open a PowerShell in the project directory and run `.\gethatch.ps1`.
PowerShell users may need to call `Set-ExecutionPolicy Unrestricted` before
running this script, and PowerShell 7 is (probably) required. I don't know anything
about Windows, so I'm not 100% sure if the other PowerShell will work or not.

The `gethatch` scripts will create a basic virtual environment in the
project directory and install hatch into it, which will make the `hatch` command
available on the commandline for the remainder of that shell session.

Hatch is a very useful tool for Python development, so if you want to install it
globally, you can follow the [installation instructions](https://hatch.pypa.io/latest/install/)
for your platform. I personally recommend using [pipx](https://github.com/pypa/pipx)
if available.

If you don't want hatch to be available globally, and you don't trust my scripts, you can
install it into an existing virtual environment with `pip install hatch`.
You can also install this project with `pip install '.[dev]'`. The `dev` option
includes `hatch` as a dependency. You don't need to worry about installing the project as editable. Once hatch is installed, it will create and manage virtual environments for the project and install the project in editable mode, so that you can iterate quickly.


### The Assignment

This project is a complete web application with everything already implemented except for the realtime websocket
routes on the backend. Specifically, the six websockets in the [chat.api.websockets.v1](./src/pykcworkshop/chat/api/websockets/v1.py) module. That python file
has the routes already declared and added to the appropriate blueprint, so the frontend can find them once they
are implemented, but they simply return a 404 right now. Your task is to implement all of the behaviors described
in the docstrings for those six websocket routes in that file.

The features that these websockets enable are as follows:

1. Realtime chat between participants in a chatroom.
2. Realtime status updates (online, typing, offline).
3. Client-Client state synchronization.
4. Infinite scroll for on-demand loading of chat history.
5. Private DMs between two members of a chatroom.
6. Realtime form validation as the user types.

Because the frontend is already built, you can run the application with `hatch run serve` and test out these
features as you implement them, but manual testing is a slow process when you are debugging or trying to solve
a new problem, so I have also written a full test suite that can be run with `hatch run test`. There are automated
tests for each of the individual requirements outlined in the docstrings for these websockets, so once all tests are
passing, the functionality should work when running the site.

The test suite is a bit slow since I had to make it run cross-platform, and testing the websockets requires spinning up
a full server. It runs in about 10-15 seconds on my Arch box. Running it in a Windows 10 VM is significantly slower. Around 30-45
seconds on my machine.

It should still be fast enough to run between each change though.

#### For the adventurous

If you have web dev experience and the workshop assignment is too easy, or if you are just curious about how I built the rest of the application, you can poke around in the other modules or the frontend and make any changes you feel like.

I intentionally structured the application to be very modular, and I separated systems by technical function as opposed to business logic/feature. This should make it easier to hack on different parts of the application based on the area of web dev that you are interested in.

A couple of suggestions for enhancements you can make:

1. (Full-stack) Add chatroom moderation features.
  - Currently, the db defines relationships for members of chatrooms, and also an owner of the chatroom (the user who created it), but there is no difference in the functionality of the application between a member and owner.
  - Adding features for the owner to be able to ban members or give different permissions within a chatroom would be a good exercise in both backend logic and frontend UX design.
2. (Frontend-focused) Make DMs show some kind of notification to the user in the UI.
  - Currently, DMs work when both users have the direct chat open, but there is no feedback when a user sends a DM, so you would never know that someone is trying to talk to you in private unless you already have the chat open.
  - This funtionality can be added without making any changes to the backend once the websockets are implemented per the requirements.
  - If you are interested in Javascript or frontend work, then figuring out how to use the existing websocket behaviors to add additonal UX on the frontend would be a good learning exercise.




### Local HTTPS

Local HTTPS can be set up with the [mkcert](https://github.com/FiloSottile/mkcert) tool.

Creat a `certs` directory in the project root and follow the installation instructions
for your platform in the mkcert READme, and then you can enable local HTTPS with the
following commands:

```bash
mkcert -install
mkcert -key-file path/to/project/root/certs/pykcworkshop-key.pem -cert-file path/to/project/root/certs/pykcworkshop.pem localhost 127.0.0.1 ::1
```

This should install a local certificate authority to your system and browser's CA store and
create a signed SSL certificate for localhost in the `certs` directory you just created in the
workshop project.

Make sure you store the certificates in the `certs` directory. This directory is in the
.gitignore file, so even if you push your changes to a public repo, it won't
upload your local certificates. Hypercorn is also configured to look for certs in this
directory when serving the application over https. That's what the genenv.py script put in the server.toml file.

To access the site over LAN from a mobile device, you'll need to include the full chain.
To find the fullchain cert run `mkcert -CAROOT`. Copy the `rootCA.pem` file from this
directory into the `certs` directory in the project root.

**Important!!** Do **NOT** copy the `rootCA-key.pem` file. That is the private key, and it must **NOT** be shared.

Once the certificates are added to the certs directory, make the following changes:

1. In the .env file, change the `SITE_ROOT` from `http://localhost:8000` to `https:localhost:8000`.
2. Open the `server.toml` file and uncomment the lines for `keyfile` and `certfile`.
3. If you added the fullchain to access the site from a phone, also uncomment the `ca-cert` line.

Now, when running `hatch run serve`, the site should be available over tls at `https://localhost:8000`.

### Project Automation

Once hatch is available, you can use it to perform the following tasks:

- Serving the application.
  - `hatch run serve`.
    - This will serve the application using the production hypercorn server.
    - The application will be hosted at `http://localhost:8000/chat`.
    - See the section on [Local HTTPS](#local-https) if you want to serve the application with tls.
- Running the test suite.
  - `hatch run test`.
    - This will start a test server with hypercorn, run the test suite, and then clean up the server process.
    - The exact commands this runs depend on the platform, but the behavior should be the same on Linux, Mac, and Windows.
    - On Windows, this requires PowerShell 7, and you may need to start the shell as an Administrator for it to run.
  - `hatch run cov`.
    - This will run the test suite just like above, but it will also generate a code coverage report and output it to the `htmlcov` directory.
    - The coverage report will be inaccurate because the test suite for this application runs a separate server process, which means that the python process running coverage.py can't detect when that server process is executing code paths in the backend.
    - This is mostly included because I just have this configuration in all of my probjects, but it's also useful for finding branches that you forgot to write a test for in areas that are actually monitored by the coverage process.
- Running the static type checker.
  - `hatch run typecheck`.
    - This will run `mypy` to check static type annotations across the entire project source.
    - This probably won't be used much for the workshop assignment, but it's helpful.
- Running the autoformatter.
  - `hatch run format`.
    - This will run `isort` and `black` over the source code and test suite.
- Running the linter.
  - Most linter errors will be resolved by running the autoformatter first, but this is useful for catching things like unused imports.
  - `hatch run lint`.
    - This will run `flake8` over the project source, the tests, and the doc generation scripts.
    - Flake8 is configured to ignore line length in the test suite since test code tends to be more verbose.
- Generating API documentation.
  - API docs are something I include in all my projects since it's generally useful and especially so when working with a team, but you probably won't use this much for this project.
  - `hatch run docs:build`.
    - This will build a static website for the API documentation from the project source.
  - `hatch run docs:serve`.
    - This will serve the static documentation website at `http://localhost:9000`.
  - `hatch run docs:test`.
    - This will run python's `doctest` over the docstrings in the project source, so any examples included in docstrings will be checked.
- Javascript Frontend.
  - The static frontend for this application is very simple, but it still has a minor build step that requires NodeJS, so you will need to install Node if you want to work on the frontend.
  - This is not required to run the application. The static frontend is already built in this repo, so you only need Node if you want to make changes to it.
  - `hatch run frontend:build`.
    - This will build the tailwind css classes and output them to a css file that the static frontend will source for its styling.
  - `hatch run frontend:format`.
    - This will run `prettier` over the frontend's source.
    - The prettier command only specifies ES6 module files (`.mjs`), so if you want to format other files, you'll need to modify the command in the pyproject.toml file.
- Workflows.
  - `hatch run ci`.
    - This will run the test suite, code coverage, typechecker, doctests, and linter all in sequence.
    - This command fails on the first failed command, so it is useful for running in a CI server where you want to conserve minutes.
    - I would recommend running this command and fixing any errors before pushing up any code to a GH repo.
  - `hatch run all`.
    - This will run all of the commands that `ci` runs as well as the autoformatter and frontend build step.
    - Unlike the `ci` command, as long as the python autoformatter runs successfully (no syntax errors in the source), then all of the other commands will run even if there are failures.
    - This should allow you to run this workflow even if you don't have Node installed.
    - This workflow is useful if you want to see all of the problems with the code all at once. For example, a failure in the test suite and a linter warning.
    - Even though this does run all sub-commands, the output of this command is not summarized, so it's still difficult to see everything if you have several failures.

#### Hatch Data

Hatch will create virtual environments and install all dependencies into them, and it will also install python interpreters if the required python versions aren't available on your machine. Hatch doesn't store anything in the project directory. Instead, it stores all of this stuff in a data directory in userspace. The default location is platform dependent, but by default, it stores everything in different sub-directories under one common parent directory. See the [hatch docs](https://hatch.pypa.io/latest/config/hatch/#directories) for the location on your platform.

Because hatch installs so much stuff for you, it can take up a decent amount of space especially if you are using a lot of separate environments or multiple interpreters. If you aren't planning on using hatch regularly, then you may choose to delete the entire directory structure where hatch stores it's stuff. There's no harm in nuking the hatch data dir. If you use hatch for something again, it will have to recreate your environments and redownload any packages and interpreters that you're missing, but it won't break your projects.
