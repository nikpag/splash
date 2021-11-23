###############################
### awk not working on pash ###
###############################
# sort by reponse codes
INPUT=${INPUT:-logs}
OUT=output_logs
run_tests() {
    # i don't think we should assign things to $0, however, it works with both
    IN=$1
    cat $IN | cut -d "\"" -f3 | cut -d ' ' -f2 | sort | uniq -c | sort -rn   
    # awk alternative, too slow
    awk '{print $9}' $IN | sort | uniq -c | sort -rn  
    # find broken links broken links
    awk '($9 ~ /404/)' $IN | awk '{print $7}' | sort | uniq -c | sort -rn  
    # for 502 (bad-gateway) we can run following command:
    awk '($9 ~ /502/)' $IN | awk '{print $7}' | sort | uniq -c | sort -r  
    # Who are requesting broken links (or URLs resulting in 502)
    awk -F\" '($2 ~ "/wp-admin/install.php"){print $1}' $IN | awk '{print $1}' | sort | uniq -c | sort -r  
    # 404 for php files -mostly hacking attempts
    awk '($9 ~ /404/)' $IN | awk -F\" '($2 ~ "^GET .*\.php")' | awk '{print $7}' | sort | uniq -c | sort -r | head -n 20  
    ##############################
    # Most requested URLs ########
    awk -F\" '{print $2}' $IN  | awk '{print $2}' | sort | uniq -c | sort -r  
    # Most requested URLs containing XYZ
    awk -F\" '($2 ~ "ref"){print $2}' $IN | awk '{print $2}' | sort | uniq -c | sort -r
}

export -f run_tests
rm -rf $OUT
mkdir -p $OUT
for f in ${INPUT}/*; do
    #bash -c 'run_tests $0 $1' $f $f #> /dev/null
    #run_tests $f > /dev/null
    logname=$OUT/$(basename $f)
    run_tests $f > $logname
done