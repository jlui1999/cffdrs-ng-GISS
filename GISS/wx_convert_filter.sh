#! /bin/sh
# @auth James Lui james.lui@nasa.gov
# @contact Robert Field robert.field@columbia.edu

# converts csv files to FWI format, filters by year(s) specified, extracts first entry above a threshold temperature, and ends with last entry above a threshold temperature

# arguments: input file, start year, end year, id (name), latitude, longitude, output file

init_fwi_values=true

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

# for the input file
# $5 TEMP_C
# $6 RH_PERC
# $8 WDSPD_KPH
# $9 PREC_MM

bash_source=$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P)

if $init_fwi_values; then
  # get the first line number that is in the start year, above 5 degrees Celcius, and also has starting FWI values
  outarr=($(awk -v ys="$yearstart" -v tt="$thresh_temp" -F, '$1 == ys && $5 != "NaN" && $5 > tt && $6 != "NaN" && $8 != "NaN" && $9 != "NaN" && $12 != "NaN" && $13 != "NaN" && $14 != "NaN" {print NR,$12,$13,$14; exit}' $infile))
  linestart=${outarr[0]}
  ffmc=${outarr[1]}
  dmc=${outarr[2]}
  dc=${outarr[3]}
else
  # get the first line number that is in the start year and also above 5 degrees Celcius
  linestart=$(awk -v ys="$yearstart" -v tt="$thresh_temp" -F, '$1 == ys && $5 != "NaN" && $5 > tt && $6 != "NaN" && $8 != "NaN" && $9 != "NaN" {print NR; exit}' $infile)
fi

if [ -z $linestart ]; then
  echo "${id}: No valid lines found"
  exit 2
fi

# get the last line number
lineendfromback=$(tac $infile | awk -v ye="$yearend" -v tt="$thresh_temp" -F, '$1 == ye && $5 != "NaN" && $5 > tt && $6 != "NaN" && $8 != "NaN" && $9 != "NaN" {print NR; exit}')
totallines=$(wc -l < $infile)
lineend=$(( $totallines-$lineendfromback+1 ))
nolines=$(( $lineend-$linestart+1 ))
#echo $nolines

# get the time zone

tz=$(python ${bash_source}/get_timezone.py -lat $lat -lon $lon) 
# get the subset of data

# header
if $init_fwi_values; then
  $(echo "id,lat,long,timezone,yr,mon,day,hr,temp,rh,ws,prec#${ffmc}#${dmc}#${dc}" | cat > $outfile)
else
  $(echo "id,lat,long,timezone,yr,mon,day,hr,temp,rh,ws,prec" | cat > $outfile)
fi

# prints the NaNs as-ias
#$(head -n $lineend $infile | tail -n $nolines | awk -v OFS=',' -v of="$outfile" -v id="$id" -v lat="$lat" -v lon="$lon" -F, '{print id,lat,lon,$1,$2,$3,$4,$5,$6,$8,$9 >> of}')

# replaces NaNs with previous value
$(head -n $lineend $infile | tail -n $nolines | awk -v OFS=',' -v of="$outfile" -v id="$id" -v lat="$lat" -v lon="$lon" -v tz="$tz" -F, '$5 == "NaN" {$5 = p7} $6 == "NaN" {$6 = p8} $8 == "NaN" {$8 = p9} $9 == "NaN" {$9 = p13} {p7 = $5} {p8 = $6} {p9 = $8} {p13 = $9} {print id,lat,lon,tz,$1,$2,$3,$4,$5,$6,$8,$9 >> of}')

# checks for discontinuities in hourly data
errorline=$(awk -F "," '{if (NR == 2) ph = $8; else if (NR > 2 && $8 != (ph + 1) % 24) {print NR; exit} else ph = $8} END {exit 0}' $outfile)

if ! [ -z $errorline ]; then
  echo "${id}: Discontinuity detected on line $errorline"
  mv $outfile ${outfile}d$errorline
fi
