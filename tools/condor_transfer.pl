#!/usr/bin/perl -w

# syntax: condor_transfert.pl executable arg path1 path2 ...
# parses command line, download files whose path is like /data/machine/raid using
# ftps under the name TPX_CONDOR_DOWNLOAD_USER if defined (default: pipeline)
# filenames have to be uniq
# when the job is done, removes all copied files, and upload remaining
# files/directories in a tar to TPX_CONDOR_UPLOAD_URL under the same user
# or recursively (keeping directories structure) if TPX_CONDOR_UPLOAD_URL is
# finished by a slash /.
#
# TPX_CONDOR_DOWNLOAD_USER and TPX_CONDOR_UPLOAD_URL have to be defined in the
# condor script using this syntax:
# environment    = TPX_CONDOR_DOWNLOAD_USER=magnard; TPX_CONDOR_UPLOAD_URL=ftp://mix8//data/mix8/raid/fred/toto.tgz
# if should_transfer_files is set to yes, then the products will also be transfered by condor.
#
# Changelog:
# 090618 FM * added --verbose --pretend --pattern --transfer_only --transfer_from_list options
# 090603 FM * changed number of parallel transfers from 2 down to 1
#           * max retry: from 5 to 10
#           * ftp_sleep_time from 2s up to 5s

use strict;
use Getopt::Long qw(:config gnu_getopt require_order);
use Pod::Usage;
use File::Spec;
use POSIX;
use Parallel::ForkManager;
use Sys::Hostname;
use File::Copy;

my $soft_name = "condor_transfert.pl";
my $version = "1.4";

my $host_pattern = 'mix\d\d?|efigix|efigix2|fcix|fcix\d|ftpix';
my $full_path_pattern = "/data/($host_pattern)/".'raid(|\d)/';
my $filenames_separator=','; # separate filenames in SExtractor's list
my $download_user =  exists($ENV{"TPX_CONDOR_DOWNLOAD_USER"}) ? $ENV{"TPX_CONDOR_DOWNLOAD_USER"} : "pipeline";
my $upload_url =  exists($ENV{"TPX_CONDOR_UPLOAD_URL"}) ? $ENV{"TPX_CONDOR_UPLOAD_URL"} : "";
my $MIN_PARALLEL_TRANSFER = 1; # defaut value if 1 host, changed to number of hosts
my $verbose=2;
my $option_curl = $verbose<=2 ? " --silent " : "";
my $ftp_tentative_number_max = 10;
my $ftp_sleep_time = 5; # seconds

# handles local options
my $help = 0;
my $pretend = 0;
my $man  = 0;
my $show_version=0;
my $transfer_only = '';
my $transfer_from_list = '';
GetOptions ('V|version'              => \$show_version,
            'h|help|?'               => \$help,
            'v|verbose+'             => \$verbose,
            'p|pretend'              => \$pretend,
            'pattern=s'              => \$full_path_pattern,
            't|transfer_only=s'      => \$transfer_only,      # comma separated list of full path /data/host/raid... files
            'l|transfer_from_list=s' => \$transfer_from_list, # file with all the files to download
            'm|man'                  => \$man
           ) || pod2usage(-message => "$soft_name version $version", -verbose => 0);
pod2usage(1) if $help;
pod2usage(-exitstatus => 0, -verbose => 2) if $man;

if ($show_version) {
  print "$soft_name version $version\n";
  exit 0;
}

my %files_to_copy = ();      # key = host, value = array of file pathes (might be duplicates)
my %files_to_remove = ();
my @newARGV = ();

my $local_hostname = hostname; $local_hostname=~s/\..*$//;
print "local_hostname = $local_hostname\n" if $verbose>=2;

#-- parse transfer_only option
if ($transfer_only) {
  my @files=split(/$filenames_separator/,$transfer_only);
  foreach my $path (@files) {
    if ($path =~ m{^$full_path_pattern}) {
      my $host = $1;
      push @{$files_to_copy{$host}}, $path;
      my ($volume,$directories,$file) = File::Spec->splitpath( $path );
      print "$file $path $host\n" if $verbose>=2;
    }
  }
}

#-- parse transfer_from_list option
if ($transfer_from_list) {
  my $path=$transfer_from_list;
  if ($path =~ m{^$full_path_pattern}) { # download file if it is remote
    my $host = $1;
    my ($volume,$directories,$file) = File::Spec->splitpath( $path );
    print "$file $path $host\n" if $verbose>=2;
#-- Now transfer file
    if ($host eq $local_hostname) {
      print "copy($path,$file)\n" if $verbose>=1;
      copy($path,$file) or die "Copy of $path failed: $!";
    } else {
      my $command = "curl $option_curl -k --ftp-ssl-control -u ${download_user}:null -E ~/.ssl/ftps.cat.pem ftp://${host}/${path} -O";
      print ("$command\n") if $verbose>=1;
      run_and_check_exit ($command);
    }
    # the file is now local, let's open it
    open LIST, $file or die("cannot open file $file: $!");
  } else { # file is already local, and can be accessed directly
    open LIST, $path or die("cannot open file $path: $!");
  }

#-- Parse the list file
  while (my $path=<LIST>) {
    chomp($path);
    $path =~ s/#.*$//;   # get rid of comments
    if ($path =~ m{^$full_path_pattern}) {
      my $host = $1;
      push @{$files_to_copy{$host}}, $path;
      my ($volume,$directories,$file) = File::Spec->splitpath( $path );
      print "$file $path $host\n" if $verbose>=2;
    }
  }
  close LIST;
}

#-- parse @ARGV, get arguments matching a local raid path, fills %files_to_copy
# with them, and fills @newARGV as the arguments to give to the program, after
# files have been copied locally
foreach my $arg (@ARGV) {
  # process also list of filenames separated by $filenames_separator
  my @files=split(/$filenames_separator/,$arg);
  my @newarg=();
  foreach my $path (@files) {
    if ($path =~ m{^$full_path_pattern}) {
      my $host = $1;
      push @{$files_to_copy{$host}}, $path;
      my ($volume,$directories,$file) = File::Spec->splitpath( $path );
      print "$file $path $host\n" if $verbose>=2;
      push @newarg, $file;
    } else {
      push @newarg, $path;
    }
  }
  push @newARGV, join($filenames_separator,@newarg);
}

#-- check for duplicate local names
my %duplicate_check = ();
for my $host (keys %files_to_copy) {
  for my $path (@{$files_to_copy{$host}}) {
    my ($volume,$directories,$file) = File::Spec->splitpath( $path );
    if (exists($duplicate_check{$file})) {
      finish("ERROR: $file appears multiple times in the list of files to process");
    }
    $duplicate_check{$file} = 1;
  }
}

#-- copy locally the files
# open as many transfers as there is hosts to transfer from
my $MAX_PARALLEL_TRANSFER =   scalar(keys(%files_to_copy)) > $MIN_PARALLEL_TRANSFER
                            ? scalar(keys(%files_to_copy))
			    : $MIN_PARALLEL_TRANSFER;
print "MAX_PARALLEL_TRANSFER = $MAX_PARALLEL_TRANSFER\n" if $verbose>=2;

my $pm = new Parallel::ForkManager($MAX_PARALLEL_TRANSFER);
my %ftp_tentative_number = ();
$pm->run_on_finish( # update the hash of files to remove at the end of the download, or manage download error
  sub { my ($pid, $exit_code, $hostpath) = @_;
    # gey host and path from forked process ident
    die ("ERROR: wrong host:path key: $hostpath") unless $hostpath =~ /([^:]+):(.*)/;
    my ($host, $path) = ($1, $2);
    my ($volume,$directories,$file) = File::Spec->splitpath( $path );
    if ($exit_code != 0) { # error !
      if (++$ftp_tentative_number{$file}>=$ftp_tentative_number_max) {
        die ("ERROR: cannot retrieve file $path from host $host, curl exit code: $exit_code");
      } else {
        # put back this file in the list of files to download and wait $ftp_sleep_time
        print STDERR "WARNING: $ftp_tentative_number{$file} th try to download file $path from host $host, still ",
               $ftp_tentative_number_max-$ftp_tentative_number{$file}," to go, next one in ", $ftp_sleep_time," sec\n"
            if $verbose>=1;
        print "WARNING: $ftp_tentative_number{$file} th try to download file $path from host $host, still ",
               $ftp_tentative_number_max-$ftp_tentative_number{$file}," to go, next one in ", $ftp_sleep_time," sec\n"
            if $verbose>=1;
        sleep $ftp_sleep_time;
        unshift @{$files_to_copy{$host}}, $path;
      }
    } else { # no error
      $files_to_remove{$file} = 1;
    }
  }
);

while (max_length(\%files_to_copy)>0) {
  while (max_length(\%files_to_copy)>0) {

    # update the number of parallel jobs
    my $nb=nb_transfer_host(\%files_to_copy);
    $pm->set_max_procs($nb>$MIN_PARALLEL_TRANSFER ? $nb : $MIN_PARALLEL_TRANSFER);
    print "updated NB of jobs = ",$nb>$MIN_PARALLEL_TRANSFER ? $nb : $MIN_PARALLEL_TRANSFER,"\n" if $verbose>=2;

    # the loop closest to the job is on hosts to optimize transfers
    for my $host (keys %files_to_copy) {
      next if scalar(@{$files_to_copy{$host}}) == 0;
      my $path = pop @{$files_to_copy{$host}};
      my ($volume,$directories,$file) = File::Spec->splitpath( $path );

      if (exists($files_to_remove{$file})) { # should not happen as we checked before
        finish("ERROR: duplicate files to process");
      }

      $pm->start($host.':'.$path) and next; # do the fork, the pid's ident being $host:$path
      if ($host eq $local_hostname) {
        print "copy($path,$file)\n" if $verbose>=1;
        if (!$pretend) {
          copy($path,$file) or die "Copy of $path failed: $!";
        }
      } else {
        my $command = "curl $option_curl -k --ftp-ssl-control -u ${download_user}:null -E ~/.ssl/ftps.cat.pem ftp://${host}/${path} -O";
        print ("$command\n") if $verbose>=1;
        run_and_check_exit ($command) unless ($pretend);
      }
      $pm->finish; # do the exit in the child process
    }
  }
  $pm->wait_all_children; # After all children came back, %files_to_copy might
     # have been refilled by the sub run_on_finish, so we include this part into
     # another while {} !
}

#-- do the real job
print "newARGV: ", join(' ',@newARGV),"\n" if $verbose>=1;
run_and_check_exit(join ' ',@newARGV) unless ($pretend);

cleanup();

#-- ftp remaining files to upload_url
if ($upload_url ne "") {
  upload_dir(".", $upload_url);
}

exit(0);

sub cleanup {
  print "files to remove: ",join("\n", keys %files_to_remove),"\n" if $verbose>=2;
  unlink keys %files_to_remove;
  %files_to_remove = (); # re-init to not try to unlink again at next call
}

sub finish {
  if ($#_ >=0) {
    print "$_[0]\n";
  }
  cleanup();
  exit(0);
}

# returns the length of the longest array as a value of hash whose ref is in arg
sub max_length {
  my ($href) = @_;
  my $l=0;
  foreach my $k (keys %$href) {
    $l = $l<scalar(@{$$href{$k}}) ? scalar(@{$$href{$k}}) : $l; 
  }
  return $l;
}

# returns the number of hosts of the hash which has files to transfer from
sub nb_transfer_host {
  my ($href) = @_;
  my $n=0;
  foreach my $k (keys %$href) {
    $n++ if scalar(@{$$href{$k}})>0;
  }
  return $n;
}

# upload $dir to $url using FTP/SSL
# if $url ends with a slash (/), a recursive copy is done (symlinks are not copied)
# if not, $dir is packed in a tar upon transfer
# The certificate located in ~/.ssl/ftps.cat.pem is used for authentication
# (compared to the remote file ~${download_user}/.tlslogin)
sub upload_dir {
  my ($dir, $url) = @_;
  # we transfer everything in a tar if the URL is not finishing with a /
  my $tarmode = $url =~ /\/$/ ? 0 : 1;

  if ($tarmode) {
    print ("tar cpz * | curl $option_curl -k --ftp-ssl-control -u ${download_user}:null -E ~/.ssl/ftps.cat.pem $url -T - \n") if $verbose>=1;
    run_and_check_exit ("tar cpz $dir | curl $option_curl -k --ftp-ssl-control -u ${download_user}:null -E ~/.ssl/ftps.cat.pem $url -T -") unless ($pretend);
  } else {
    opendir DIR, $dir or die("cannot open dir $dir");
    my @dircontent = readdir DIR;
    closedir DIR or die("cannot close dir $dir");

    # get rid of leading .. and/or . for upload dir (non tar mode)
    my @d=split(/\//,$dir);
    while (defined($d[0]) && ($d[0] eq "." || $d[0] eq ".." || $d[0] eq "")) {shift @d};
    my $remote_dir = join('/',@d);
    $remote_dir .= '/' unless $remote_dir =~ /\/$/;

    my @files_list = sort grep { -f "$dir/$_"} @dircontent;
    if (@files_list != 0) {
      my $command = "curl $option_curl --ftp-create-dirs -k --ftp-ssl-control -u ${download_user}:null -E ~/.ssl/ftps.cat.pem $url$remote_dir -T \"{".join(',',@files_list)."}\"";
      print "running $command\n" if $verbose>=1;
      my $current_dir = getcwd;
      chdir $dir;
      run_and_check_exit("$command") unless ($pretend);
      chdir $current_dir;
    }

    foreach my $dirname (sort grep {-d "$dir/$_" && !($_ eq "." || $_ eq "..")} @dircontent) {
      upload_dir("$dir/$dirname","$url");
    }
  }
  return 1; # success if it went that far
}

###############################################
# ARGS: 
#  $command (or a list to be concatenated): shell command to run
# Output:
#  none if success in execution
# Purpose: 
#   execute a command in a shell and check its exit status
#   dies if exit status is non zero
#   POSIX compliant (need use POSIX)
###############################################
sub run_and_check_exit {
  local $SIG{'CHLD'}; # desactivate CHLD catching to access $?
  my ($command) = join(' ',@_);
  system($command);
  if (WIFEXITED($?)) { # child process exited normally
    WEXITSTATUS($?) != 0 # exit status of the child not = 0
      && die ("ERROR: the following command returned the non zero value "
              .WEXITSTATUS($?).":\n$command\n");
  } else {
    WIFSIGNALED($?)    #  child process terminated because of a signal
      && die ("ERROR: the following command exited because of signal "
              .WTERMSIG($?).":\n$command\n");
    die ("ERROR: the following command failed to exit normally:\n$command\n");
  }
}

__END__

=head1 NAME

B<condor_transfert.pl> - Condor files transfer wrapper

=head1 SYNOPSIS

B<condor_transfert.pl> [B<-h>|B<--man>] [B<-v>] [B<-V>] [B<-p>] [B<--pattern> full_path_pattern] [B<-t> path1[,path2[,path3...]]] [B<-l> remote_file_list] -- command option1 option2 ...

=head1 DESCRIPTION

B<condor_transfert.pl> is a wrapper which parses condor command lines, and downloads files whose path is like /data/machine/raid using ftps under the name TPX_CONDOR_DOWNLOAD_USER if defined (default: pipeline).

Filenames have to be uniq.

When the job is done, removes all copied files, and upload remaining
files/directories in a tar to TPX_CONDOR_UPLOAD_URL under the same user
or recursively (keeping directories structure) if TPX_CONDOR_UPLOAD_URL is
finished by a slash /.

TPX_CONDOR_DOWNLOAD_USER and TPX_CONDOR_UPLOAD_URL have to be defined in the
condor script using this syntax:

 environment    = TPX_CONDOR_DOWNLOAD_USER=magnard; TPX_CONDOR_UPLOAD_URL=ftp://mix8//data/mix8/raid/fred/toto.tgz

If should_transfer_files is set to yes, then the products will also be transfered by condor.

=head1 OPTIONS

=over 4

=item B<-V|--version>

shows version number

=item B<-m|--man>

shows this man page

=item B<-v|--verbose>

verbose option : the higher -v option you give, the more details are reported.

=item B<-p|--pretend>

does not transfer (except the file list if any) or execute anything, but shows what would be done (needs verbose >= 1).

=item B<--pattern> full_path_pattern

perl pattern used to identify remote files to transfer (the hostname pattern has to be between parenthesis ()). Quoting might be tricky...

E.g.: /data/(mix\d\d?|efigix|efigix2|fcix|fcix\d|ftpix)/raid(|\d)/

=item B<-t|--transfer_only> path1[,path2[,path3...]]

list of remote files to transfer, without keeping them in the command line to execute (useful for .ahead files when scamping)

=item B<-l|--transfer_from_list> remote_file_list

remote_file_list is a (maybe remote) list of files to transfert only (its path must match the remote file pattern or it will be considered local)

=head1 EXAMPLE

=head1 SEE ALSO

=head1 DEPENDENCIES

 - File::Spec package for perl: http://search.cpan.org/dist/PathTools
 - Parallel::ForkManager package for perl: http://search.cpan.org/~dlux/
 - curl http://curl.haxx.se/

=head1 AUTHOR

 Frédéric Magnard
 Terapix - Institut d'Astrophysique de Paris
 Report bugs to <magnard@iap.fr>

 Copyright 2009 Terapix
 This  is free software; under Gnu Public License

=cut

