#!/bin/zsh

# The data looks like this:
# 1,    2,                   3,   4,                       5
# epoch,categorical_accuracy,loss,val_categorical_accuracy,val_loss
# 0,0.717691484422,0.88959204055,0.674169921875,0.95098362565
EPOCH=1
ACC=2
VAL_ACC=4

location="${2:-$(realpath ~easantos/training-grammar-guru/models)}"
csvfile="$location/training.log"
device="${1:-dumb}"

if [ -s "$csvfile" ] ; then
    csvfile="$(realpath "$csvfile")"
else
    echo "Not a valid training log: $csvfile" 1>&2
    exit -1
fi

gnuplot -p <<EOF
set terminal ${device}
set datafile separator ','

set title 'Accuracy: training vs. validation '
set xlabel 'Epoch'
set ylabel 'Accuracy'
set yrange [0:1]
set key bmargin

plot "${csvfile}" using ${EPOCH}:${ACC}     title 'Train' with lines, \
     "${csvfile}" using ${EPOCH}:${VAL_ACC} title 'Validation' with lines
EOF

printf '%5s\t%12s\t%12s\t%11s\t%12s\n' 'Epoch' 'Acc' 'Val. Acc' 'Loss' 'Val. Loss'
<"${csvfile}" awk -F, 'NR > 1 {
    printf "%5d\t%11.2f%%\t%11.2f%%\t%11f\t%11f\n", $1, 100.0 * $2, 100.0 * $4, $2, $5
}'
