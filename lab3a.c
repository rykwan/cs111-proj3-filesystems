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
__u32 blockSize;
struct ext2_group_desc* blockgroups = NULL;

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
  blockSize = EXT2_MIN_BLOCK_SIZE << superblock.s_log_block_size;

  printf("SUPERBLOCK,%d,%d,%d,%d,%d,%d,%d\n",
    superblock.s_blocks_count,
    superblock.s_inodes_count,
    blockSize,
    superblock.s_inode_size,
    superblock.s_blocks_per_group,
    superblock.s_inodes_per_group,
    superblock.s_first_ino);
}

void groupSummary(int fd) {
  const __u32 superblockSize = sizeof(struct ext2_super_block);
  __u32 bgtable_blockno = superblockSize / blockSize + 1;
  const __u32 offset = bgtable_blockno * blockSize;
  __u32 numgroups = 1 + (superblock.s_blocks_count-1) / superblock.s_blocks_per_group;

  unsigned int gdesc_size = sizeof(struct ext2_group_desc);
  unsigned int i;
  __u32 blocks_in_group = 0;
  blockgroups = malloc(numgroups * gdesc_size);
  for ( i = 0; i < numgroups; i++ ) {
    pread(fd, &blockgroups[i], gdesc_size, offset + i*gdesc_size);
    if ( i == numgroups - 1 )
      blocks_in_group = superblock.s_blocks_count % superblock.s_blocks_per_group;
    else
      blocks_in_group = superblock.s_blocks_per_group;
    printf("GROUP,%d,%u,%u,%u,%u,%u,%u,%u\n",
	   i,
	   blocks_in_group,
	   superblock.s_inodes_per_group,
	   blockgroups[i].bg_free_blocks_count,
	   blockgroups[i].bg_free_inodes_count,
	   blockgroups[i].bg_block_bitmap,
	   blockgroups[i].bg_inode_bitmap,
	   blockgroups[i].bg_inode_table
	   );
  }
}

void freeBlockEntries() {
  __u32 numGroups = 1 + (superblock.s_blocks_count-1) / superblock.s_blocks_per_group;
  struct ext2_group_desc group;

  for (unsigned int i = 0; i < numGroups; i++) {
    group = blockgroups[i];
    __u32 bitmap = group.bg_block_bitmap;
    int blocks_in_group;
    if ( i == numGroups - 1 )
      blocks_in_group = superblock.s_blocks_count % superblock.s_blocks_per_group;
    else
      blocks_in_group = superblock.s_blocks_per_group;

    int currBlock = 0;
    while (currBlock < blocks_in_group) {
      if (bitmap & 0x01) {
        printf("BFREE,%d\n", currBlock);
      }
      bitmap = bitmap >> 1;
      currBlock++;
    }
  }
}

int main(int argc, char **argv) {
  int fsfd = processArgs(argc, argv); // file system image

  superblockSummary(fsfd);
  groupSummary(fsfd);
  freeBlockEntries();

  if ( blockgroups != NULL )
    free(blockgroups);
  close(fsfd);
  exit(0);
}
