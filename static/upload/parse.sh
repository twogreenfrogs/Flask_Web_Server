#!/bin/bash
# 07/18/2016: add -i option for case insensitive seach option
# example:
# ./parse_log.sh -e -i "DLC_SystemLog_Archived_2016-0*" "3G_MGR"
# ./parse_log.sh -f -i "DLC_SystemLog_Archived_2016-0*" "port_mgr*" "3G_MGR"

usage() {
        echo 'usage: ./parse.sh -e/-f [-i] "TAR_FILES" [FILE_NAME] "SEARCH_STRINGS"'
	echo ' -i: case insensitive in grep command'
	echo ' -e: use egrep and search SEARCH_STRINGS in all files under current dir'
	echo ' -f: use find to find specific file FILE_NAME and search SEARCH_STRINGS'
        echo ' ex1: ./parse_log.sh -e "DLC_SystemLog_Archived_2016-0*" "3G_MGR"'
        echo ' ex2: ./parse_log.sh -f -i "DLC_SystemLog_Archived_2016-0*" "port_mgr*" "3G_MGR"'
	echo	
	exit 0
}

if [ "$1" == "-e" ]
then
	if [ $# -eq 3 ]
	then
        	OPTION=""
        	TAR_FILES=$2
        	SEARCH_STR=$3
	elif [ $# -eq 4 ]
	then
        	OPTION=$2
        	TAR_FILES=$3
        	SEARCH_STR=$4
	else
		usage
	fi

elif [ "$1" == "-f" ]
then
        if [ $# -eq 4 ]
        then
                OPTION=""
                TAR_FILES=$2
                FILE=$3
                SEARCH_STR=$4
        elif [ $# -eq 5 ]
        then
                OPTION=$2
                TAR_FILES=$3
                FILE=$4
                SEARCH_STR=$5
	else
		usage	
	fi

else
        usage
fi

echo "option: $1, Num of Args: $#"
echo "checking tarball: $TAR_FILES..."
echo "with option ${OPTION}..."
echo "searching ${FILE}..."
echo "and grepping ${SEARCH_STR}..."
OUTFILE=$(pwd)"/output.txt"
OUTFILE_TEMP=$OUTFILE"_temp"
echo 

rm -rf $OUTFILE
rm -rf $OUTFILE"_temp"

for f in $(ls $TAR_FILES)
do
        dir=$(echo $f | awk -F '.' '{ print $1 }')
        rm -rf $dir 2> /dev/null
        mkdir $dir
        cp $f $dir
        cd $dir
        echo "untar $f..."
        tar -xvzf $f > /dev/null 2>&1
        #cat log/dla.log | egrep -i "ai-systest.digitallife.att.com|exception binding|Connectivity|IOException" | tee -a $OUTFILE
        #cat log/dla.log | egrep "unable to setup socket|Error sending roundtrip|HEARTBEAT_FAILED|exception binding" | tee -a $OUTFILE
        #cat log/dla.log | egrep -i "connectToSocket: SUCCESS|connectToSocket: IOException getting socket|connectivity" | tee -a $OUTFILE
        #cat log/dla.log | egrep ${OPTION} "$SEARCH_STR" | tee -a $OUTFILE
        #grep "Battery \[Disonnect\]|Battery \[Disconnect\]" /var/log/*

	if [ "$1" == "-e" ]
	then	
        	egrep ${OPTION} "${SEARCH_STR}" ./ -r 2> /dev/null | tee -a $OUTFILE_TEMP
        
	else
		find ./ -name ${FILE} -exec egrep ${OPTION} "${SEARCH_STR}" {} \; | tee -a $OUTFILE_TEMP
       	fi
 
	cd ..
        rm -rf $dir
        sleep 0.5
done

sort $OUTFILE_TEMP | uniq > $OUTFILE
rm -rf $OUTFILE_TEMP
mv ${OUTFILE} ${OUTFILE}"_$SEARCH_STR"
echo "done..."
echo
echo 
cat ${OUTFILE}"_$SEARCH_STR"
exit 0
