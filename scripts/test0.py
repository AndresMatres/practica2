from pathlib import Path

path = Path('/home')
fpath = path / 'andres' / 'Desktop' / 'projecto' / 'read_stats'


def get_samples_from_file(fhand):
    samples = {}
    for sample in fhand:
        sample.rstrip()
        samples[sample] = {}
    
    return(samples)


def _get_reads_number_from_fastqc(fhand):
    for line in open(fhand):
        if line.startswith('Total Sequences'):
            line = line.rstrip()
            fields = line.split('\t')
            total_seq_for_mate_read = int(fields[1])
                
    


def get_total_reads_from_fastqc_report(fpath, sample, kind=None):
    total_reads = []

    for item in fpath.iterdir():
        if item.name == kind and item.is_dir():
            reports_folder = item

            for report in reports_folder.iterdir():
                if report.name.startswith(sample):
                    for file_ in report.iterdir():
                        if file_.name == 'fastqc_data.txt':
                            total_reads_for_mate = _get_reads_number_from_fastqc(open(file_)) # barrabaja para indicar que la funcion es privada
                            total_reads.append(total_reads_for_mate)
                            

    return(total_reads)


def get_total_clean_reads(fpath):
    total_clean_reads = []

    for child in fpath.iterdir():
        if child.name == 'clean':
            clean = child

            for cleans in clean.iterdir():
                for files in cleans.iterdir():
                    if files.name == 'fastqc_data.txt':
                        for line in open(files):
                            line = line.rstrip()
                            fields = line.split('\t')

                            if fields[0] == 'Total Sequences':
                                total_seq = (int(fields[1]))*2
                                if total_seq not in total_clean_reads:
                                    total_clean_reads.append(total_seq)
    
    return(total_clean_reads)


def create_stats(stats, total_raw_reads, total_clean_reads):
    n = -1
    for key in stats.keys():
        n += 1
        sample = stats[key]
        raw_reads = total_raw_reads[n]
        clean_reads = total_clean_reads[n]
        stats[key] = {'total_raw_reads':raw_reads, 'total_clean_reads':clean_reads}
    
    print(stats)
    return(stats)




def main():
    do_test = False
    if do_test:
        pass
    else:
        stats = get_samples_from_file(fhand)
        for sample in stats:
            total_raw_reads = get_total_reads_from_fastqc_report(fpath, sample, kind='raw')
            total_clean_reads = get_total_reads_from_fastqc_report(fpath, sample, kind='clean')
        
        results = create_stats(stats, total_raw_reads, total_clean_reads)

if __name__ == '__main__':
 	main()
