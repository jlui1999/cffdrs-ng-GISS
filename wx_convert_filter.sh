#! /bin/sh

# converts csv files to FWI format, filters by year(s), extracts first entry with >5C, and ends with last entry >5C

# arguments: inputfile, start year, end year, outputfile

infile=$1
yearstart=$2
yearend=$3
id=$4
lat=$5
lon=$6
outfile=$7

thresh_temp=5

# get the first line number that is in the start year and also above 5 degrees Celcius
linestart=$(awk -v ys="$yearstart" -v tt="$thresh_temp" -F, '$1 == ys && $7 != "NaN" && $7 > tt {print NR; exit}' $infile)
#echo $linestart

# get the last line number
lineendfromback=$(tac $infile | awk -v ye="$yearend" -v tt="$thresh_temp" -F, '$1 == ye && $7 != "NaN" && $7 > tt {print NR; exit}')
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
