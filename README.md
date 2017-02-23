The following steps can be used to run this extract / transform program.

1. Create initial extract of TOC entries

```
./extract_toc.py --files ../in/*.txt --detail conf/detail.csv --summary conf/summary.csv --distinct conf/distinct.csv
```

2. Create a map.csv from distinct TOC entries in distinct.csv. Simply add a third column to denote the TOC entry to be used for final data file. You may add de-dup logic here. A map.csv is already constructed in the conf directory. If you change that, simply re-run the subsequent steps.

3. Create a ML mapper model for TOC entries using Random Forest

```
./create_toc_mapper_rf.py --map conf/map.csv --savemodel conf/model01.pkl
```

4. Analyze available ratings data in the files to create a ratings map.

```
./get_ratings.py --files ../in/*.txt --out conf/file_ratings.txt --distinct conf/distinct_ratings.txt
cp conf/distinct_ratings.txt conf/ratings_map.txt
```

Now edit the file `conf/ratings_map.txt`. It has all the distinct rating columns (as evaluated by the parser) per line.
Add a second column to the file like below:
  a. Enter NA if you think this is not a valid rating name
  b. Keep-as is if the rating name is valid and is not a duplicate
  c. For names that should point to another name in the file (logical duplicate), enter the pointer name
This file will be referred to as the Ratings Map file in the subsequent sections.

5. Analyze subtopic for "IT Analysis" topic

  5.1 First time analysis (for quick viewing only):

  ```
  ./analyze_topic.py --files ../in/*.txt --topic 'IT Assessment' --summary conf/summary.csv --model conf/model01.pkl --print_detail
  ```

  5.2 Get all subtopics for first time model analysis

  ```
  ./analyze_topic.py --files ../in/*.txt --topic 'IT Assessment' --summary conf/summary.csv --model conf/model01.pkl --print_summary > conf/IT_Assessment_Subtopics_Raw.csv
  ```

  5.3 Edit `IT_Assessment_Subtopics_Raw.csv` in excel. The first column is normalized (lowercased, unnecessary characters removed) subtopic, 2nd column is blank, the rest of the columns are actual correspinding subtopic names as appeared in the documents. Fill the 2nd column with the appropriate subtopic category / name, this provides the user an opportunity to group and de-dup same subtopics differing by author preferences. Save this file in `conf/IT_Assessment_Subtopics.csv`

  5.4 Generate models. Both Random Forest and Support Vector Machine is supported, the latter works better with this dataset.

  ```
  ./create_subtopic_mapper.py --map conf/IT_Assessment_Subtopics.csv --savemodel conf/model_sub_svc.pkl --alg svc
  ./create_subtopic_mapper.py --map conf/IT_Assessment_Subtopics.csv --savemodel conf/model_sub_rf.pkl --alg rf
  ```

  5.5 Analysis when we get subsequent files. These files may have the same subtopics or different ones. We review how our model translates these and if needed, augment the model.

  ```
  ./analyze_topic.py --files ../in/*.txt --topic 'IT Assessment' --summary conf/summary.csv --model conf/model01.pkl --print_summary | \
    ./check_for_new_subtopics.py --model conf/model_sub_svc.pkl --out conf/new_subtopics.csv
  ```

  If new subtopics are reported, they will be placed in `conf/new_subtopics.csv`. Check this file for correctness of mapping. If not satisfied, add the bad lines to file `IT_Assessment_Subtopics.csv` with the corrected name in the 2nd column and re-run the model generation process (step 5.4). At the end, verify the last command again.


6. Create the final CSV extract file. Because the CSV contains columns that contain more than 32K characters (a Microsoft Excel Limitation) and they are also multiline, there are a few command line options to control the output format and layout.

```
--model <Model File>            Model File created in previous step
--files <Input Files>           All input files
--summary <Summary File>        Summary file created in step 1
--out <Output File>             Output file name
--split <n>                     Number of times (denoted by n) each topic is split
                                into multiple columns.
                                e.g. if n is 2, a topic "Conclusions" will be in two
                                columns, Conclusions_1 and Conslusions_2 with a 32K
                                max character in each column.
                                By default, n is 4, unless the nosplit option is
                                specified
--nosplit                       If this option is specified, the topic columns are
                                not split. This might create a file that is not
                                viewable in Microsoft Excel. However, Python and R
                                should be able to read this file.
--rmap                          Name of the Ratings Map file
--NL <Newline Chars>            If you would like to not have multiline columns
                                create a line break in the output you can use
                                this option to specify a character or set of
                                characters that replace the newlines within a
                                column.
--fd <Field Delimiter>          Custom field delimiter, typically used for Hive e.g. --fd '~'
--fdr <Delimiter Sub>           Replace field delimiter in data with this value, typically used for Hive. e.g. --fdr '-'
--err                           Exception file name. All non-FDIC exams (identified
                                 by absence of part 309 clause) are listed here.
--smodels <Model File>         Subtopic model file generated in step 5.4. Use this option if you wish to generate separate columns for subtopics
--stopics <Topic Name>         Topic name (e.g. "IT Assessment") for shich subtopics are to be extracted. Use this option if you
                               wish to generate separate columns for subtopics
```

The following are some examples:

Create a multi column output (4 columns per topic)

```
./get_headers.py --model conf/model01.pkl --files ../in/*.txt --summary conf/summary.csv --rmap conf/ratings_map.txt --out out/files_parsed_multicol_multiline.csv --err out/non_fdic_exam_files.txt
```
Create a multi column, single line output (newlines replaced by \n)

```
./get_headers.py --model conf/model01.pkl --files ../in/*.txt --summary conf/summary.csv --NL '\n' --rmap conf/ratings_map.txt --out out/files_parsed_multicol_singleline.csv --err out/non_fdic_exam_files.txt
```

Create a single column, single line output

```
./get_headers.py --model conf/model01.pkl --files ../in/*.txt --summary conf/summary.csv --nosplit --NL '\n' --rmap conf/ratings_map.txt --out out/files_parsed_singlecol_singleline.csv --err out/non_fdic_exam_files.txt
```

Create a single column, multi line output

```
./get_headers.py --model conf/model01.pkl --files ../in/*.txt --summary conf/summary.csv --nosplit --rmap conf/ratings_map.txt --out out/files_parsed_singlecol_multiline.csv --err out/non_fdic_exam_files.txt
```

Create a single column, single line output with Subtopics

```
./get_headers.py --model conf/model01.pkl --files ../in/*.txt --summary conf/summary.csv --nosplit --NL '\n' --rmap conf/ratings_map.txt --out out/files_parsed_singlecol_singleline.csv --err out/non_fdic_exam_files.txt --smodels conf/model_sub_svc.pkl --stopics 'IT Assessment'
```

You can also tune the following parameters at the top of file `get_headers.py`

```
NEWLINE_WITHIN_COLUMN = '\r\n'
CSV_LINE_TERMINATOR = '\r\n'
CSV_FIELD_DELIMITER = ','
```

The following script files are created for easy running of the last step.
```
1. run_all_headers.sh
2. run_all_headers_with_subtopics.sh
```
