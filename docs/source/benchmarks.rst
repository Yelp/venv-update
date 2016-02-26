.. _benchmarks:

Benchmarks
==========

You can find the set of scripts used to derive these numbers at:
https://github.com/Yelp/venv-update/tree/master/benchmark

benchmark: installing plone and its dependencies (260 packages)
last run: [2016-02-24]

::

    pip8:
        cold:   
            4m37.612s
            4m39.762s
            4m39.717s
        noop:
            0m6.890s
            0m7.112s
            0m7.436s
        warm:
            0m44.684s
            0m44.614s
            0m43.272s


    pip-faster:
        cold:
            4m16.163s
            4m21.282s
            4m14.038s
        noop:
            0m2.399s
            0m2.389s
            0m2.335s
        warm:
            0m30.410s
            0m21.303s
            0m21.323s
