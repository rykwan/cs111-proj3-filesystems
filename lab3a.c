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
#include <time.h>

#include "ext2_fs.h" /* describes ext2 file system */

struct ext2_super_block superblock;
__u32 blockSize;
struct ext2_group_desc* blockgroups = NULL;

#define BASE_OFFSET 1024  /* location of the super-block in the first group */
#define BLOCK_OFFSET(block) (BASE_OFFSET + (block-1)*blockSize)

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
  __u32 bgtable_blockno = (1023+superblockSize) / blockSize + 1;
  //  const __u32 offset = bgtable_blockno * blockSize;
  const __u32 offset = BLOCK_OFFSET(bgtable_blockno);
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

#define BLOCK_ENTRIES 1
#define INODE_ENTRIES 2
void printFreeEntries(int fd, int entry) {
  __u32 numGroups = 1 + (superblock.s_blocks_count-1) / superblock.s_blocks_per_group;
  struct ext2_group_desc group;

  unsigned int i;
  for ( i = 0; i < numGroups; i++) {
    group = blockgroups[i];

    int blocks_in_group;
    if ( i == numGroups - 1 )
      blocks_in_group = superblock.s_blocks_count % superblock.s_blocks_per_group;
    else
      blocks_in_group = superblock.s_blocks_per_group;

    __u32 bitmapAddress = (entry == BLOCK_ENTRIES) ? group.bg_block_bitmap : group.bg_inode_bitmap;
    __u32 * bitmap = malloc(blocks_in_group + 32 - (blocks_in_group % 32)); // allocate another index (plus 32) just in case
    pread(fd, bitmap, blocks_in_group/8, BLOCK_OFFSET(bitmapAddress));

    int currBlock = 1;
    int j= 0;
    while (currBlock <= blocks_in_group) {
      if (!(bitmap[j] & 0x01)) {
	if ( entry == BLOCK_ENTRIES )
	  printf("BFREE,%d\n", currBlock);
	else
	  printf("IFREE,%d\n", currBlock);
      }
      bitmap[j] >>= 1;
      if (currBlock % 32 == 0)
	j++;
      currBlock++;
    }

    free(bitmap);
  }
}

void direEntries(int fd) {
  __u32 numGroups = 1 + (superblock.s_blocks_count-1) / superblock.s_blocks_per_group;
  struct ext2_group_desc* group;

  unsigned int i;
  for ( i = 0; i < numGroups; i++) {
    group = &blockgroups[i];

    int blocks_in_group;
    if ( i == numGroups - 1 )
      blocks_in_group = superblock.s_blocks_count % superblock.s_blocks_per_group;
    else
      blocks_in_group = superblock.s_blocks_per_group;

    int j;
    for ( j = 0; j < blocks_in_group; j++) {
      struct ext2_inode inode;
      int blockno = group->bg_inode_table;
      pread(fd, &inode, sizeof(struct ext2_inode), BLOCK_OFFSET(blockno) + j * sizeof(struct ext2_inode));
      if ( (inode.i_mode & 0x4000) == 0x4000 ){
	unsigned char* currblock = malloc(blockSize);
	pread(fd, currblock, blockSize, BLOCK_OFFSET(inode.i_block[0]));
	__u32 nbytes = 0;
	struct ext2_dir_entry *dentry = (struct ext2_dir_entry *) currblock;
	if (dentry->inode != 0) {
	  while (nbytes < 512){//  inode.i_size) { ///TODO: i_size
	    char filename[EXT2_NAME_LEN + 1];
	    memcpy(filename, dentry->name, dentry->name_len);
	    filename[dentry->name_len] = '\0';
	    printf("DIRENT,%d,",j+1);
	    printf("%u,%u,%u,%u,'%s'\n",nbytes,dentry->inode, dentry->rec_len, dentry->name_len, filename);
	    nbytes += dentry->rec_len;
	    dentry = (void *) dentry + dentry->rec_len;
	  }
	}
	free(currblock);
	/** TODO: If the entries list takes more than one block, the program will crash***/
      }
    }
  }
}

void inodeSummary(int fd) {
  __u32 numGroups = 1 + (superblock.s_blocks_count-1) / superblock.s_blocks_per_group;

  for (__u32 g = 0; g < numGroups; g++) {
    struct ext2_group_desc *group = &blockgroups[g];
    for (__u32 i = 2; i < superblock.s_inodes_count; i++) {
      struct ext2_inode *inode = NULL;
      pread(fd, inode, sizeof(struct ext2_inode), BLOCK_OFFSET(group->bg_inode_table) + (i-1) * sizeof(struct ext2_inode));

      // Determine file type
      char ftype = '?';
      if (inode->i_mode & 0x8000)
        ftype = 'f';
      else if (inode->i_mode & 0x4000)
        ftype = 'd';
      else if (inode->i_mode & 0xA000)
        ftype = 's';

      // Get low order 12 bits for mode
      __u16 mode = inode->i_mode & 0xFFF;

      // Convert time to human readable strings
      char* changeTimeStr = NULL;
      char* modTimeStr = NULL;
      char* accessTimeStr = NULL;
      time_t changeTime = (time_t)inode->i_ctime;
      time_t modTime = (time_t)inode->i_mtime;
      time_t accessTime = (time_t)inode->i_atime;
      strftime(changeTimeStr, 100, "%D %T", gmtime(&changeTime));
      strftime(modTimeStr, 100, "%D %T", gmtime(&modTime));
      strftime(accessTimeStr, 100, "%D %T", gmtime(&accessTime));

      if (inode->i_mode != 0 && inode->i_links_count != 0) {
        printf("INODE,%d,%c,%o,%d,%d,%d,%s,%s,%s,%d,%d\n",
          i,
          ftype,
          mode,
          inode->i_uid,
          inode->i_gid,
          inode->i_links_count,
          changeTimeStr,
          modTimeStr,
          accessTimeStr,
          inode->i_size,
          inode->i_blocks);
      }
    }
  }
}


int main(int argc, char **argv) {
  int fsfd = processArgs(argc, argv); // file system image

  superblockSummary(fsfd);
  groupSummary(fsfd);
  printFreeEntries(fsfd, BLOCK_ENTRIES);
  printFreeEntries(fsfd, INODE_ENTRIES);
  inodeSummary(fsfd);
  direEntries(fsfd);

  if ( blockgroups != NULL )
    free(blockgroups);
  close(fsfd);
  exit(0);
}
