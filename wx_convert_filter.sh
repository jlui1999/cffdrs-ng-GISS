#! /bin/sh
# @auth James Lui james.lui@nasa.gov
# @contact Robert Field robert.field@columbia.edu

# converts csv files to FWI format, filters by year(s) specified, extracts first entry above a threshold temperature, and ends with last entry above a threshold temperature

# arguments: input file, start year, end year, id (name), latitude, longitude, output file
#
if [ $# -ne 7 ]; then
  echo "Required arguments needed: 7, provided: $#"
  echo "<wx input file> <year start> <year end> <id/name> <lat> <long> <output file>"
  exit 1
fi

infile=$1
yearstart=$2
yearend=$3
id=$4
lat=$5
lon=$6
outfile=$7

thresh_temp=5

# get the first line number that is in the start year and also above 5 degrees Celcius
linestart=$(awk -v ys="$yearstart" -v tt="$thresh_temp" -F, '$1 == ys && $7 != "NaN" && $7 > tt && $8 != "NaN" && $9 != "NaN" && $13 != "NaN" {print NR; exit}' $infile)
#echo $linestart

if [ -z $linestart ]; then
  echo "${id}: No valid lines found"
  exit 0
fi

# get the last line number
lineendfromback=$(tac $infile | awk -v ye="$yearend" -v tt="$thresh_temp" -F, '$1 == ye && $7 != "NaN" && $7 > tt && $8 != "NaN" && $9 != "NaN" && $13 != "NaN" {print NR; exit}')
totallines=$(wc -l < $infile)
lineend=$(( $totallines-$lineendfromback+1 ))
nolines=$(( $lineend-$linestart+1 ))
#echo $nolines

# get the subset of data

# header
$(echo "id,lat,long,yr,mon,day,hr,temp,rh,ws,prec" | cat > $outfile)

# prints the NaNs as-ias
#$(head -n $lineend $infile | tail -n $nolines | awk -v OFS=',' -v of="$outfile" -v id="$id" -v lat="$lat" -v lon="$lon" -F, '{print id,lat,lon,$1,$2,$3,$4,$7,$8,$9,$13 >> of}')

# replaces NaNs with previous value
$(head -n $lineend $infile | tail -n $nolines | awk -v OFS=',' -v of="$outfile" -v id="$id" -v lat="$lat" -v lon="$lon" -F, '$7 == "NaN" {$7 = p7} $8 == "NaN" {$8 = p8} $9 == "NaN" {$9 = p9} $13 == "NaN" {$13 = p13} {p7 = $7} {p8 = $8} {p9 = $9} {p13 = $13} {print id,lat,lon,$1,$2,$3,$4,$7,$8,$9,$13 >> of}')

# checks for discontinuities in hourly data
errorline=$(awk -F "," '{if (NR == 2) ph = $7; else if (NR > 2 && $7 != (ph + 1) % 24) {print NR; exit} else ph = $7} END {exit 0}' $outfile)

if [ -n $errorline ]; then
  echo "${id}: Discontinuity detected on line $errorline"
  mv $outfile ${outfile}d$errorline
fi
