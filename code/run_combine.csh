#!/bin/csh -f
foreach x (phenix_faqs.list phenix_overviews.list   phenix_top_level.list   phenix_misc.list        phenix_reference.list   phenix_tutorials.list)
echo "working on ${x:r}"
cp $x discovered_urls.txt
phenix.python combine.py discovered_urls.txt > combine_b.html
cat combine_a.html combine_b.html combine_c.html > combine_${x:r}.html
echo "DONE with ${x:r}"
end
