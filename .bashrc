# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# User Setting For Cygwin
alias firefox="/cygdrive/c/Program\ Files\ \(x86\)/Mozilla\ Firefox/firefox.exe"
alias winpy="/cygdrive/c/Python27/python.exe"

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
HISTCONTROL=ignoreboth:erasedups

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=1000
HISTFILESIZE=2000

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
#force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# some more aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

alias chrome='chromium-browser & 2>/dev/null;if [ ! $? ];then chromium & 2>/dev/null;fi;if [ ! $? ];then echo "command not found";fi '
alias cdo="cd \$OLDPWD"
alias hi='echo -e "\n****HISTORY****"; fc -rl -15|awk '\''{print  " -"NR"  "$2" "$3" "$4" "$5" "$6" "$7}'\'';echo "";\
read -p "Choose number >" var ; if [ $var -ne 0 ] 2>/dev/null;then fc -s -${var}; fi;'


# Add an "alert" alias for long running commands.  Use like so:
#   sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi


# User define 
PATH+=:$HOME/scripts:$HOME/py/codes


# List cahanged directory
function shift_cdarray(){
	array=()
	array[0]=0
	for i in {0..15};do
		array[`expr $i + 1 `]=${cd_array[$i]}
	done
	cd_array=(`echo ${array[@]}`)
}

cd_array=()
function cd(){
	shift_cdarray
	cd_array[0]=$PWD
	command cd $1
}

function cdh(){
	echo -e "\n****HISTORY OF CHANGE-DIRECTORY****"
	num=0
	for i in `echo ${array[@]}`;do
		echo ${cd_array[$num]} |awk -v num=`expr $num + 1` '{print " -"num"  "$0}'
		num=`expr $num + 1`
	done

	echo ""
	read -p "Choose number >" var 
	if [ $var -ne 0 ] 2>/dev/null && [ $var -le 15 ] ;then 
		command cd ${cd_array[`expr $var - 1`]}
	fi
}
#************************
# Lynx direct search
function lynxs(){
	queryStr=`echo $@|tr ' ' '+'`
	lynx http://www.google.co.jp/search?q\=${queryStr}
}

# Monitor the file that will be overwritten by CgiPrograms
echo -n "" >>~/www/text/lines.txt
#tail -n 0 -f ~/www/text/lines.txt &

#English-Japanese Dictionaly
DICTIONARY=$HOME"/Document/dictionary.txt"
function dict(){
	if [ ! "$1" ];then
		echo -n -e "\n\t検索文字列 : ";
		read String;
	else 
		String=$1;
	fi
	grep -w $String $DICTIONARY|awk -F '[\t/;]' -v String=$String 'BEGIN{printf ("\n")};//{if (String ~ /^[a-zA-Z]+$/){printf ("%s%s%s\n",NR,":\t",$0)} else {printf ("%s%s%s%s",NR,": ",$1,"\t\t");for (i=1;i<=NF;i++){if ($i ~ String ){printf ("%s",$i)}};printf ("\n")}}'
}

#lookをgrepで色付けするだけ
function look(){
	if [ "$2" ];then
		echo "This is Overwrittened Function by bashrc file"
		return 1
	elif [ ! "$1" ];then
		echo -n -e "\n\t検索文字列 : ";
		read String;
	else 
		String=$1;
	fi
	command look $1 |grep $1
}
	

#My shopt
shopt -s cdspell
shopt -s dirspell
HISTIGNORE=fg*:bg*:ls:exit:shutdown*:hi*:cdh:cd*:firefox
PROMPT_COMMAND=""

#Setting for Git
#Set Completion
if [ -f $HOME/.git-completion.bash ];then
	source $HOME/.git-completion.bash
fi
#Set Prompt
PROMPT_COMMAND="Set_Git_PS1;"${PROMPT_COMMAND}
DEFAULT_PS1=${PS1}
function Set_Git_PS1(){
	if [ -d $PWD/.git ];then
		now_branch=`git branch |grep "*"|sed 's/\* //'`
#		echo -en '\e[33m('$now_branch')\e[m'
		PS1='\u@\h:\w\e[1;34m ('$now_branch')\e[m$ '
	else
		PS1=${DEFAULT_PS1}
	fi
}


