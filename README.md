sshuttle
========
sshuttle allows you to keep a familiar environment with you when you connect to new hosts.

It works by inject shell fragments into your remote system environment prior to launching your shell.

how does it work?
=================
sshuttle searches your home directory (~/.sshuttlerc and ~/.shuttlerc.d/*) for rc files which contain arbitrary shell fragments.

These fragements are compiled into a URI encoded string which is written to a temp file on the remote system when your ssh connection is established. After the rc file is written, your shell process is replaced, pointing to your temporary rc file.

Here's an example of the injection string:
```
INJECT="mkdir /tmp/sshuttle.40780; echo \$(python -c 'import urllib; import sys; print urllib.unquote(str(sys.argv[1]))' 'rm%20%24TMPDIR/.rc%3B_EOLrmdir%20%24TMPDIR%3B_EOLPS1%3D%22%5C%5B%5Ce%5B00%3B31m%5C%5D%5Cu%5C%5B%5Ce%5B0m%5C%5D%5C%5B%5Ce%5B00%3B37m%5C%5D%40%5C%5B%5Ce%5B0m%5C%5D%5C%5B%5Ce%5B00%3B36m%5C%5D%5Ch%5C%5B%5Ce%5B0m%5C%5D%5C%5B%5Ce%5B00%3B37m%5C%5D%3A%5Cw%20%5C%5B%5Ce%5B0m%5C%5D%22_EOL_EOL%23%20following%20sourced%20from%20/Users/kinnj028/.sshuttlerc_EOLexport%20PS1%3D%22%5C%5B%5Ce%5B00%3B37m%5C%5D%5Cu%40%5CH%3A%5CW%20%5C%5B%5Ce%5B0m%5C%5D%22_EOLset%20-o%20vi_EOL_EOLhello_function%28%29%20%7B_EOL%20%20%20%20echo%20%22HELLO%20THERE%22_EOL%7D_EOL_EOLhello_function_EOL%23%20following%20sourced%20from%20/Users/kinnj028/.sshuttlerc.d/aliases_EOL%23%20aliases_EOLalias%20%27..%27%3D%27cd%20..%27_EOLalias%20%27...%27%3D%27cd%20../..%27_EOLalias%20%27....%27%3D%27cd%20../../..%27_EOL%23%20following%20sourced%20from%20/Users/kinnj028/.sshuttlerc.d/two_EOL%23%20arbitrary%20text') | sed 's/_EOL/\n/g' >/tmp/sshuttle.40780/.rc"; /usr/bin/ssh -t hostname "$INJECT; TMPDIR=/tmp/sshuttle.40780 exec /bin/bash --rcfile /tmp/sshuttle.40780/.rc"
```

installation
============
```
git clone git://github.com/justinkinney/sshuttle
python setup.py install
```

example usage
=============

First, populate ~/.sshuttlerc with some commands:
```
export PS1="\[\e[00;37m\]\u@\H:\W \[\e[0m\]"
set -o vi

hello_function() {
    echo "HELLO THERE"
}

hello_function
```

Then, test your ssh connection. Your prompt and other script contents should be available in your new session:
```
$ sshuttle hostname
HELLO THERE
username@hostname.example.com:~
```

You can also throw files into ~/.sshuttlerc.d to be included:
```
$ cat ~/.sshuttlerc.d/aliases
# aliases
alias ls='ls -F'
alias ll='ls -lh'
alias lt='ls --human-readable --size -1 -S --classify'
alias gh='history|grep'
```

TODO
====
* sshuttle should infer the shell to launch on the remote system, probably from the rc file shebang line
