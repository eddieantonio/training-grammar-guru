#!/bin/zsh

# The data looks like this:
# 1,    2,                   3,   4,                       5
# epoch,categorical_accuracy,loss,val_categorical_accuracy,val_loss
# 0,0.717691484422,0.88959204055,0.674169921875,0.95098362565
EPOCH=1
ACC=2
VAL_ACC=4

SCRIPT_NAME="${0##*/}"

# Adapated from:
# http://mywiki.wooledge.org/BashFAQ/035#CA-485294e4ff594e7d9e7c9c09b4d4110339260cf7_1
show_help() {
    cat <<EOF
Usage:
    ${SCRIPT_NAME} [--model=MODEL] [--display=DISPLAY|--qt] [PATH_TO_MODEL_DIR]
    ${SCRIPT_NAME} [--list]

Displays status on the accuaracy of the models or lists the models.

    --help      show this screen and exit
    --list      lists the existing models
    --model     specify a model using N1,N2,...,Nn notation
    --display   passed directly into gnuplot's terminal argument
EOF
}

show_list() {
    ls -d ~easantos/Backups/models/*/
}

device="dumb"
model=

while :; do
    case $1 in
        -h|--help)   # Call a "show_help" function to display a synopsis, then exit.
            show_help
            exit
            ;;
        -l|--list)   # Call a "show_help" function to display a synopsis, then exit.
            show_list
            exit
            ;;
        -m|--model)       # Takes an option argument, ensuring it has been specified.
            if [ -n "$2" ]; then
                model=$2
                shift
            else
                printf 'ERROR: "--model" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;
        --model=?*)
            model=${1#*=} # Delete everything up to "=" and assign the remainder.
            ;;
        --model=)         # Handle the case of an empty --model=
            printf 'ERROR: "--model" requires a non-empty option argument.\n' >&2
            exit 1
            ;;
        -d|--device)       # Takes an option argument, ensuring it has been specified.
            if [ -n "$2" ]; then
                device="$2"
                shift
            else
                printf 'ERROR: "--device" requires a non-empty option argument.\n' >&2
                exit 1
            fi
            ;;
        --device=?*)
            device=${1#*=} # Delete everything up to "=" and assign the remainder.
            ;;
        --device=)         # Handle the case of an empty --model=
            printf 'ERROR: "--device" requires a non-empty option argument.\n' >&2
            exit 1
            ;;
        --qt)
            device=qt
            ;;
        --)              # End of all options.
            shift
            break
            ;;
        -?*)
            printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
            ;;
        *)               # Default case: If no more options then break out of the loop.
            if [ -n "$1" ] ; then
                location="$1"
            fi
            break
            ;;
    esac
    shift
done

location="${location:-$(realpath ~easantos/training-grammar-guru/models)}"
csvfile="$location/training.log"

if [ ! -s "$csvfile" ] ; then
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
