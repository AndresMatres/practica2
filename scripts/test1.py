import sys
from pathlib import Path
import subprocess

# final_results = {"sample1": {"total_raw_reads": 10,  "total_clean_reads": 5, "primary_reads_aligned": 10, "secondary_reads_aligned": 20}}
# las variables estas van arriba y en mayusculas xq son variables globales que se pueden usar en cualquier sitio
PROJECT_DIR = Path(sys.argv[1])
READS_REPORT_DIR = PROJECT_DIR / 'read_stats'
BAM_FILES_DIR = PROJECT_DIR / 'mapping'
ORIGINAL_MAPPING_DIR = BAM_FILES_DIR / 'original'
FILTERED_MAPPING_DIR = BAM_FILES_DIR / 'filtered'
REPORTS_DIR = PROJECT_DIR / 'reports'
DEDUP_DIR = BAM_FILES_DIR / 'filtered'


def get_samples_from_file(fhand):
    samples = {}
    for sample in open(fhand):
        sample = sample.rstrip()
        samples[sample] = {}
    
    return(samples)


def _get_reads_number_from_fastqc(fhand): # barrabaja para indicar que la funcion es privada
    for line in fhand:
        if line.startswith('Total Sequences'):
            line = line.rstrip()
            fields = line.split('\t')
            total_seq_for_mate_read = int(fields[1])
    return total_seq_for_mate_read
                

def get_total_reads_from_fastqc_report(fpath, sample, kind=None):
    total_reads = []

    for item in fpath.iterdir():
        if item.name == kind and item.is_dir():
            reports_folder = item

            for report in reports_folder.iterdir():
                if report.name.startswith(sample):
                    for file_ in report.iterdir():
                        if file_.name == 'fastqc_data.txt':
                            total_reads_for_mate = _get_reads_number_from_fastqc(open(file_)) 
                            total_reads.append(total_reads_for_mate)

    if len(total_reads) != 2:
     	raise ValueError("The number of reports for this sample is different than two!: {}".format(sample))
    if total_reads[0] != total_reads[1]:
        raise ValueError("Total reads from one mate is different than in the other mate's report: {}".format(sample))
    return(total_reads[0])


def _parse_results_from_flagstat(stdout, samples_stats, sample, kind=None):
    stdout_position = 0
    for line in stdout:
        if stdout_position == 0:
            total_reads = int(line.split()[0])
        
        elif stdout_position == 1:
            secondary_reads = int(line.split()[0])
            primary_reads = total_reads - secondary_reads
        stdout_position += 1
    if kind == 'mapping':
        samples_stats[sample]["primary reads aligned"] = primary_reads
        samples_stats[sample]["secondary reads aligned"] = secondary_reads
    if kind == 'dedup':
        samples_stats[sample]["primary alignments deduplicated"] = primary_reads
        samples_stats[sample]["secondary alignments deduplicated"] = secondary_reads
                        
        


def get_reads_from_bamfiles(fpath, samples_stats):
    for bamfile in fpath.iterdir():
        for sample in samples_stats:
            if bamfile.name.startswith(sample):
                flagstats = ['samtools', 'flagstat', '-@', '6', bamfile] # el -@ 6 hace que vaya mas rapido
                stdout = subprocess.check_output(flagstats).decode().split('\n')
                if fpath == ORIGINAL_MAPPING_DIR:
                    _parse_results_from_flagstat(stdout, samples_stats, 
                                                    sample, kind='mapping')
                elif fpath == DEDUP_DIR:
                    _parse_results_from_flagstat(stdout, samples_stats, 
                                                    sample, kind='dedup')

    return(samples_stats)


def test_get_total_reads_from_fastqc_report():
    fpath = PROJECT_DIR
    sample = 'Nt1_S1'
    total_raw_reads = get_total_reads_from_fastqc_report(fpath, sample, kind='raw')
    assert total_raw_reads == 55252796


def test_get_reads_from_bamfiles():
    samples_stats = {'Nt1_S1':{}, 'Nt2_S2':{}, 'Nt3_S3':{}}
    samples_stats = get_reads_from_bamfiles(ORIGINAL_MAPPING_DIR, samples_stats)
    samples_stats = get_reads_from_bamfiles(DEDUP_DIR, samples_stats)
    assert samples_stats['Nt1_S1']['secondary reads aligned'] == 338353
    assert samples_stats['Nt2_S2']['primary alignments deduplicated'] == 41134


def create_stats_table_lines(stats):
    stats_table_lines = []
    for sample in stats:
        sample_stats = stats[sample]

        total_raw_reads = sample_stats['total raw reads']
        total_clean_reads = sample_stats['total clean reads']
        perc_remaining_reads_after_cleaning = round(total_clean_reads/total_raw_reads, 2) # redondea a los 2 decimales

        primary_alignments = sample_stats['primary reads aligned']
        secondary_alignments = sample_stats['secondary reads aligned']
        perc_remaining_clean_reads_from_mappping = round(primary_alignments/total_clean_reads, 2)

        primary_alignments_dedup = sample_stats['primary alignments deduplicated']
        perc_remaining_clean_reads_dedup = round(primary_alignments_dedup/total_clean_reads, 2)
        secondary_alignments_dedup = sample_stats['secondary alignments deduplicated']
        perc_remaining_secondary_alignments_dedup = round(secondary_alignments_dedup/secondary_alignments, 2)

        perc_remaining_reads_from_raw_reads = round(primary_alignments_dedup/total_raw_reads, 2)

        stats_table_line = '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t\t{}'.format(sample,
                                                                            total_raw_reads,
                                                                            total_clean_reads,
                                                                            perc_remaining_reads_after_cleaning,
                                                                            primary_alignments,
                                                                            perc_remaining_clean_reads_from_mappping,
                                                                            secondary_alignments,
                                                                            primary_alignments_dedup,
                                                                            perc_remaining_clean_reads_dedup,
                                                                            secondary_alignments_dedup,
                                                                            perc_remaining_secondary_alignments_dedup,
                                                                            perc_remaining_reads_from_raw_reads)

        stats_table_lines.append(stats_table_line)
    
    return(stats_table_lines)


def draw_stats_table(stats_table_lines):
    stats_table = open(PROJECT_DIR / 'stats.csv','w')
    headers_section = '\tCleaning\t\t\tMapping\t\t\tDeduplication\n'
    cleaning_section = 'samples\ttotal raw reads\ttotal clean reads\t'
    cleaning_section += '% ' + 'remaining reads after cleaning\t'
    mapping_section = 'Primary alignments (clean reads mapped and properly paired)\t'
    mapping_section += '% ' + 'of Remaining clean reads from mapping\tNumber of extra alignments\t'
    dedup_section = 'Primary alignments (properly mapped reads, deduplicated)\t'
    dedup_section += '% ' + 'of remaining clean reads from mapping and deduplication\tNumber of extra alignments, deduplicated\t'
    dedup_section += '% ' + 'of Remaining secondary alignments from deduplication\t\t' + '% ' + 'of remaning reads from raw reads'
    header = headers_section + cleaning_section + mapping_section + dedup_section
    stats_table.write(header + '\n')
    for line in stats_table_lines:
        stats_table.write(line + '\n')


def main():
    print('hola')
    do_test = False
    if do_test:
       test_get_total_reads_from_fastqc_report()
       test_get_reads_from_bamfiles()
    else:
        samples_file = sys.argv[2]

        stats = get_samples_from_file(samples_file)
        #stats_dedup = get_samples_from_file(samples_file)
        for sample in stats:
            stats[sample]["total raw reads"] =  get_total_reads_from_fastqc_report(READS_REPORT_DIR, sample, kind='raw')
            stats[sample]["total clean reads"] = get_total_reads_from_fastqc_report(READS_REPORT_DIR, sample, kind='clean')

        stats = get_reads_from_bamfiles(ORIGINAL_MAPPING_DIR, stats)
        stats = get_reads_from_bamfiles(DEDUP_DIR, stats)
        
        stats_table_lines = create_stats_table_lines(stats)
        draw_stats_table(stats_table_lines)
        
        #print(stats)
        #print(stats_dedup)

if __name__ == '__main__':
 	main()


# se puede hacer nueva stats_dedup si descomento lo que hay comentado en el main y cambio la segunda stats a stats_dedup