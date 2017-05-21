"Setting for Windows-Cygwin 
let pythonPath = "/cygdrive/c/Python27/python.exe" 

"global variables for switching function mode
let programing_lang=""
let filename=""
let comment_char=""
let command_list=[" ci = Clear Indent"," co = Comment Out"," db = DeBag"," cd = Clear Debag line"]
let keylist=split("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_",'\zs')
let vimfile=expand("~/vimdata")
let bufferFile=g:vimfile.'/bufferedFileslog'

"Read module script
source ~/vimdata/source/func_module.vim

"Initialize processing
call Interpret_programinglang()
let filename=expand("%:t")[0:match(expand("%:t"),"\\.")-1]


"Set option----
set number
set ruler
set showmatch
set showcmd

set cursorline
set cursorcolumn
set autoindent 
set smartindent
set copyindent
set showmode
"set wrapmargin=5
set linebreak
"set mouse=a
"set mousefocus
set preserveindent
set showbreak=-
"set complete
"set lines=35
"set columns=88
"For debag set autowrite
set backup
set backupdir=~/vimdata/backup/
execute "set dictionary=".g:vimfile."/dictionary/".g:programing_lang."-dict"
set complete+=k
set complete-=t
set completeopt=menuone
set pumheight=8
set incsearch
set wildmenu
"set ignorecase

"etcOprtions
syntax on
highlight CursorColumn ctermbg=Black


"ifsection
if g:programing_lang!=""
	execute "set tags=".g:vimfile."/tags/".g:programing_lang."tags"
endif


"Key mapping--------
inoremap jj <Esc>
nnoremap <silent> ci :call Clearindent("dummy")<CR>
nnoremap <silent> co :call Commentout("dummy")<CR>
nnoremap <silent> db :call Debagline()<CR>
nnoremap <silent> exe :call Execute("dummy")<CR>
nnoremap <silent> <C-m> 'm
nnoremap <silent> <C-a> 'a
inoremap <expr> <Tab> Clevertab()
inoremap <expr> <CR> Clevercr()
nnoremap <silent> <Space><Space> :call FileOpener(0)<CR>
inoremap <C-l> <RIGHT>
inoremap <C-h> <LEFT>

cabbrev cd Cleardebagline
cabbrev exe Execute

if g:programing_lang=="HTML"
	inoremap <expr> > HtmlTagComplete()
endif

"Own command-------
command Execute call Execute("from command")
"command -nargs=1 Clearindent call Clearindent(<f-args>)
"command -nargs=1 Commentout call Commentout(<f-args>)
"command Cleardebagline call Cleardebagline()
"
if g:programing_lang!=""
	command Ctags execute "!ctags -Rf ".g:vimfile."/tags/".g:programing_lang."tags "expand("%:p:h")."/*".expand("%:e")
endif

"Auto command--------
if g:programing_lang!=""
	autocmd InsertCharPre * call Autocomplete(v:char)
endif
autocmd BufEnter * call Initialize_variable()

"Initialize all variable related opning file status
function Initialize_variable()
	call Interpret_programinglang()
	execute "set dictionary=".g:vimfile."/dictionary/".g:programing_lang."-dict"

	if g:programing_lang!=""
		execute "set tags=".g:vimfile."/tags/".g:programing_lang."tags"
	endif
	if g:programing_lang=="HTML"
		inoremap <expr> > HtmlTagComplete()
	endif
	if g:programing_lang!=""
	command! Ctags execute "!ctags -Rf ".g:vimfile."/tags/".g:programing_lang."tags "expand("%:p:h")."/*".expand("%:e")
	endif

	"Add the opninglog to logfile
	if expand("%")!="" && match(expand("%:t"),"vimFile")==-1 && expand("%:p")!=g:bufferFile && expand("%:p") !~ "/usr/share/vim" 
		"if 'opening FILENAME match in bufferfile',then output the content of worked-bufferfile ,that pulled out the FILENAME. Or output raw-content of bufferfile to temporaly file
		execute 'silent !if [ -n "`grep '.expand('%:p').' '.g:bufferFile.'`" ];then cat '.g:bufferFile.'|awk -v expr="'.expand('%:p').'" ''//{if ( $0 \!~ expr ){print $0}}'' >/tmp/tmp ; cat /tmp/tmp |tail -n 30 >'.g:bufferFile.';fi'
		execute 'silent !echo '.expand('%:p').' >>'.g:bufferFile
	
	endif
endfunction


"Own function----------
"for clear indent
function Clearindent(linenum)
	if a:linenum=="dummy"
		.<
	elseif a:linenum!="dummy" 
 		for i in range(getpos(".")[1],a:linenum+getpos(".")[1]-1)
			execute(i."<")
		endfor
	endif
endfunction

"Commentout line
function Commentout(linenum)
	let poslist=getpos(".")
	let poslist[2]=0

	"clear commentout
	if g:comment_char=="//"
		if getline(".")[0:1]==g:comment_char 
			call setpos(".",poslist)
			execute "normal xx"
			return 0
		endif
	endif
	if getline(".")[0]==g:comment_char 
		call setpos(".",poslist)
		execute "normal x"
		return 0
	endif

	"Do comment out
	if a:linenum=="dummy" 
		call setpos(".",poslist) 
		execute('normal i'.g:comment_char)
	elseif a:linenum!="dummy"
		for i in range(poslist[1],a:linenum+poslist[1]-1)
			let poslist[1]=i
			call setpos(".",poslist) 
			execute('normal i'.g:comment_char)
		endfor

	endif
endfunction

"for defining selected line as debag line 
function Debagline()
	let strnum=len(getline("."))+indent(".")+1
	let poslist=getpos(".")
	let poslist[2]=strnum
	
	call setpos(".",poslist)        
	execute('normal a       '.g:comment_char.'For debag')

endfunction

"for delete debug all line
function Cleardebagline()
	let nowpos=getpos(".")
	for linenum in range(1,getpos("$")[1])
		let line=getline(linenum)
		if len(line)!=0
			if match(line,g:comment_char.'For debag$')!=-1 
				let poslist=[0,linenum,0,0]                
				"let poslist[2]=match(line,'For debag$')

				call setpos(".",poslist)
				execute("normal o")
				call setpos(".",poslist)
				execute("normal dd")

			endif
		endif
	endfor
	call setpos(".",nowpos)
endfunction

"execute the editing file 
function Execute(flag)
	call Interpret_programinglang()
	execute "w"
	if g:programing_lang=="Python"
		execute "!".g:pythonPath." %"
	
	elseif g:programing_lang=="C"
		if a:flag=="dummy"
"			execute "!gcc -o ../out/".g:filename.".out %"
			execute "!gcc %;./a.exe"
		elseif a:flag=="from command"
			execute "!../out/".g:filename.".out"
		endif
	
	elseif g:programing_lang=="HTML"
		execute "!firefox %"

	elseif g:programing_lang=="Javascript"
		execute "! touch /tmp/".expand("%:t")."\.html ; echo -e \'<\\!DOCTYPE HTML>\\n<html><head>\\n<meta http-equiv=\"Content-Type\" content=\"text/html;charset=utf-8\">\\n<script type=\"text/javascript\" src=\"".expand("%:p")."\"></script>\\n</head></html>' >/tmp/".expand("%:t")."\.html ;firefox /tmp/".expand("%:t")."\.html & "
	
	elseif g:programing_lang=="Shellscript"
		execute "!".getline(".")

	else
		echo "this langage code is not defineded"
	endif
endfunction

"this function call then type anykey (in :autocompletemode==True
function Autocomplete(char)
	if !Listin(a:char,g:keylist)
		return 0
	elseif match(getline("."),g:comment_char)==0||pumvisible() != 0
		for key in g:keylist
			execute "inoremap <silent> ".key." ".key
		endfor
		return 0
	else 
		for key in g:keylist
			execute "inoremap <silent> ".key." ".key."\<C-n>\<C-p>"
		endfor
	endif

endfunction

"this funtion return complete command when complete popupmenu is visible
function Clevertab()
	if pumvisible()==0
		return "\<Tab>"
	elseif pumvisible()!=0
		return "\<C-n>"

	endif
endfunction

"like upword
function Clevercr()
	if pumvisible()==0
		return "\<CR>"
	elseif pumvisible()!=0
		return "\<C-y>"

	endif
endfunction

"insert html endtag
function HtmlTagComplete()
	let tag=""
	if match(getline("."),"<")!=-1
		let tag=getline(".")[match(getline("."),"<")+1:match(getline(".")," ")]
	endif

	let firstmatch=match(getline("."),"<")
	if tag=="" || match(getline("."),"<",firstmatch+1)!=-1 || tag=="br" ||tag=="hr"||tag=="meta"
		return ">"
	else
		return "></".tag.">".RepeatString("\<LEFT>",len(tag)+2)
	endif
endfunction

function Completecouple(char)
	if a:char=="*" && getline(".")[getpos(".")[2]-2]=="/"
		return '\*\*/\<LEFT>\<LEFT>'
	elseif a:char=="("
		return "()\<LEFT>"
	elseif a:char=="["
		return "[]\<LEFT>"
	elseif a:char=="{"
		return "{}\<LEFT>"
	elseif a:char=='"'
		return "\"\"\<LEFT>"
	elseif a:char=="'"
		return "''\<LEFT>"
	elseif a:char=="<"
		return "<>\<LEFT>"

	else
		return a:char
	endif
endfunction


"File opener--
let FileOpener_Opend=[0,0]
let FileOpener_StartingPos=[0,3,1,0]
function FileOpener(dotOption,...)
	if a:0==0
		let g:OpningFileDir=(exists("g:OpningFileDir")? g:OpningFileDir : expand("%:p:h"))
		let g:preOpningFileDir=(exists("g:preOpningFileDir")? g:preOpningFileDir : g:OpningFileDir)
	endif
	if !g:FileOpener_Opend[0]||a:dotOption==1||(a:0==1 && a:1=="Clear Dot Option")
		execute 'silent !echo -e "----- Quick File Opener -----\t\tCurrent at: '.g:OpningFileDir.'" >/tmp/vimFileOpener'
		execute 'silent !echo "\" Opning File Directory" >>/tmp/vimFileOpener;find '.g:OpningFileDir.' -maxdepth 1 -type f'.(a:dotOption?"":'|awk ''//{if ($0 \!~ /\/\.[^\/]*$/){print $0}}'' ').' >>/tmp/vimFileOpener'
		if expand($PWD) != g:OpningFileDir
			execute 'silent !echo -e "\n\" Current working directory" >>/tmp/vimFileOpener;find $PWD -maxdepth 1 -mindepth 1 -type f'.(a:dotOption?"":'|awk ''//{if ($0 \!~ /\/\.[^\/]*$/){print $0}}'' ').' >>/tmp/vimFileOpener'
		endif
		execute 'silent !echo -e "\n\" Buffer log" >>/tmp/vimFileOpener;cat -n '.g:bufferFile.'|sort -r |cut -f 2 |while read line;do if [ -f $line ];then echo $line;fi;done >>/tmp/vimFileOpener;'
	endif
	if a:0==1
		edit /tmp/vimFileOpener
	else 
		split /tmp/vimFileOpener
	endif

	call FileOpener_initialize()
	let g:FileOpener_Opend[0]=1
	nnoremap <buffer> <silent> . :call FileOpener(1,"Apply Dot Option")<CR>
	nnoremap <buffer> <silent> u :call FileOpener(0,"Clear Dot Option")<CR>
endfunction

function FileOpener_initialize()
	setlocal nonumber
	setlocal nocursorcolumn
	
	nnoremap <buffer> <silent> <CR> :call FileOpener_Open("CR")<CR>
	nnoremap <buffer> <silent> l :call FileOpener_Open("CR")<CR>
	nnoremap <buffer> <silent> s :call FileOpener_Open("s")<CR>
	nnoremap <buffer> <silent> q :q<CR>
	nnoremap <buffer> <expr> j CleverMove("\<Down>")
	nnoremap <buffer> <expr> k CleverMove("\<Up>")
	nnoremap <buffer> <silent> n :call NextComment()<CR>

	nnoremap <buffer> <silent> <Space> :call FileOpener_browser(0)<CR>
	unmap <Space><Space>
	autocmd BufUnload <buffer> nnoremap <silent> <Space><Space> :call FileOpener(0)<CR>
	nnoremap <buffer> i <RIGHT><LEFT>

	syntax region Type start='"' end="\n"
	syntax match Keyword /\/[a-zA-Z_\.\-0-9]*$/hs=s+1
	syntax region Comment start='-----' end='-----'
	syntax region Constant start='Current at:' end="\n"
	call setpos(".",g:FileOpener_StartingPos)
	execute "normal \<C-l>"
endfunction

function FileOpener_Open(key)
	let l:line=getline(".")
	"For Directory Open
	if a:key=="h"
		let l:line=g:OpningFileDir[0:match(g:OpningFileDir,"\/[^\/]*$")-1]
		call FileOpener_browser(0,l:line)
	elseif a:key=="u"
		let l:line=g:preOpningFileDir
		call FileOpener_browser(0,l:line)
	elseif a:key=="."
		let l:line=g:OpningFileDir
		call FileOpener_browser(1,l:line)
	elseif match(getline("."),"Directory")==0
		let l:line=line[10:]
		call FileOpener_browser(0,l:line)
	else
		"For File Open
		execute "q"
		if a:key=="CR"
			execute "tabe ".l:line
		elseif a:key=="s"
			execute "vsplit ".l:line
		endif
		"for OpningFileDir
		if line[strlen(line)-1]=='/'
			let l:line=line[0:match(line,"\/[^/]*\/[^/]*$")-1]
		else
			let l:line=line[0:match(line,"/\[^/]*$")-1]
		endif
		let g:FileOpener_Opend=[0,0]

		execute "normal \<C-w>\<C-x>"
	endif
	let g:preOpningFileDir=g:OpningFileDir
	let g:OpningFileDir=l:line
endfunction

function CleverMove(str)
	let numlist=(a:str=="\<Down>"?[2,2]:[-1,2])
	if getline(getpos(".")[1]+numlist[0])[0]=='"' 
		return RepeatString(a:str,numlist[1])
	else
		return a:str
	endif
endfunction

function NextComment()
	for linenum in range(getpos(".")[1],getpos("$")[1])
		if linenum==getpos("$")[1]
			call setpos(".",g:FileOpener_StartingPos)
		elseif match(getline(linenum),'"')==0
			call setpos(".",[0,linenum+1,1,0])
			break
		endif
	endfor
	execute "normal zt"
	execute "normal \<C-Y>"
endfunction

function FileOpener_browser(dotOption,...)
	if !g:FileOpener_Opend[1] && a:0==0 
		execute 'silent !echo -e "----- File Browser -----\t\tCurrent at: '.g:OpningFileDir.'" >/tmp/vimFileBrowser'
		execute 'silent ! echo "\" Opning File Directory" >>/tmp/vimFileBrowser;find '.g:OpningFileDir.' -maxdepth 1 -mindepth 1 -type d|awk ''//{if ($0 \!~ /\/\.[^\/]*$/){print "Directory "$0}}'' >>/tmp/vimFileBrowser'
		execute 'silent !if [ `ls '.g:OpningFileDir[0:match(g:OpningFileDir,"\/[^\/]*$")-1].'|wc -l` -gt 1 ];then echo -e "\n\" :'.(g:OpningFileDir[0:match(g:OpningFileDir,"\/[^\/]*$")-1]).'" >>/tmp/vimFileBrowser;find '.(g:OpningFileDir[0:match(g:OpningFileDir,"\/[^\/]*$")-1]).' -maxdepth 1 -mindepth 1 -type d|awk ''//{print "Directory "$0}'' >>/tmp/vimFileBrowser;fi'
		if expand($PWD) != g:OpningFileDir
			execute 'silent ! echo -e "\n\" Point of Working Directory" >>/tmp/vimFileBrowser;find $PWD -maxdepth 1 -mindepth 1 -type d|awk ''//{if ($0 \!~ /\/\./){print Directory $0}}'' >>/tmp/vimFileBrowser'
		endif
		let g:FileOpener_Opend[1]=1
	elseif a:0==1
		let l:line=a:1
		execute 'silent !echo -e "-----File Browser-----\t\tCurrent at: '.l:line.'\n\"'.l:line.'" >/tmp/vimFileBrowser_Opened;find '.l:line.' -maxdepth 1 -mindepth 1 -type d'.(a:dotOption? "" : '|awk ''//{if ($0 \!~ /\/\.[^\/]*$/){print $0}}'' ').'|awk ''//{print "Directory "$0}'' >>/tmp/vimFileBrowser_Opened;find '.l:line.' -maxdepth 1 -mindepth 1 -type f'.(a:dotOption? "" : '|awk ''//{if ($0 \!~ /\/\.[^\/]*$/){print $0}}'' ').' >>/tmp/vimFileBrowser_Opened;'
		execute 'silent !if [ `ls '.l:line[0:match(l:line,"\/[^\/]*$")-1].'|wc -l` -gt 1 ];then echo -e "\n\" :'.(l:line[0:match(l:line,"\/[^\/]*$")-1]).'" >>/tmp/vimFileBrowser_Opened;find '.(l:line[0:match(l:line,"\/[^\/]*$")-1]).' -maxdepth 1 -mindepth 1 -type d'.(a:dotOption? "" : '|awk ''//{if ($0 \!~ /\/\.[^\/]*$/){print $0}}'' ').'|awk ''//{print "Directory "$0}'' >>/tmp/vimFileBrowser_Opened;fi'
		let g:FileOpener_Opend[1]=2
	endif

	if g:FileOpener_Opend[1]==1
		edit /tmp/vimFileBrowser
	elseif g:FileOpener_Opend[1]==2
		edit /tmp/vimFileBrowser_Opened
	endif

	call FileOpener_initialize()
	syntax keyword Type Directory
	nnoremap <buffer> <silent> <Space> :call FileOpener(0,"Open from browser")<CR>
	nnoremap <buffer> <silent> u :call FileOpener_Open("u")<CR>
	nnoremap <buffer> <silent> h :call FileOpener_Open("h")<CR>
	nnoremap <buffer> <silent> . :call FileOpener_Open(".")<CR>
endfunction

