/*
 * NAME: Sanketh Hedge, Raymond Kwan
   EMAIL: shegde20@ucla.edu, raykwan@ucla.edu
   ID: 604788993, 304783893
 */

#include <stdint.h>
#include <unistd.h> /* pread(2), write(2) */
#include <stdio.h> /* fprintf */
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h> /* open(2) */
#include <errno.h>
#include <string.h>

#include "ext2_fs.h" /* describes ext2 file system */

struct ext2_super_block superblock;

int processArgs(int argc, char **argv) /* returns fd of file image */{
  char usage[28] = "Usage: ./lab3a fs_image";
  if ( argc > 2 ) {
    fprintf(stderr,"Too many arguments. %s\n", usage);
    exit(1);
  }
  else if ( argc < 2 ) {
    fprintf(stderr,"Too few arguments. %s\n", usage);
    exit(1);
  }
  int fd = open(argv[1], O_RDONLY);
  if ( fd < 0 ){
    fprintf(stderr,"Error opening file image. %s\n", strerror(errno));
  }
  dup(fd);
  return fd;
}

void superblockSummary(int fd) {
  pread(fd, &superblock, sizeof(struct ext2_super_block), 1024);
  __u32 blockSize = EXT2_MIN_BLOCK_SIZE << superblock.s_log_block_size;

  printf("SUPERBLOCK,%d,%d,%d,%d,%d,%d,%d\n",
    superblock.s_blocks_count,
    superblock.s_inodes_count,
    blockSize,
    superblock.s_inode_size,
    superblock.s_blocks_per_group,
    superblock.s_inodes_per_group,
    superblock.s_first_ino);
}

int main(int argc, char **argv) {
  int fsfd = processArgs(argc, argv); // file system image

  superblockSummary(fsfd);

  close(fsfd);
  exit(0);
}
