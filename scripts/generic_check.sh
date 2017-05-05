run_check_pipe() {
	step="$1"
	outf=/tmp/coiotd_checks

	echo -ne "\033[1;33m*\033[0m $step: "
	sh >$outf 2>&1
	r=$?

	if [ $r -ne 0 ]; then
		echo -e "\033[91mFailed\033[0m"
		cat $outf
	else
		echo -e "\033[32mOK\033[0m"
	fi

	return $r
}

run_check_script() {
	cat "$2" | run_check_pipe "$1"
}
