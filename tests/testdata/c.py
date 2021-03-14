# Borrowed for testing with real test data from the linux kernel source.
# https://github.com/torvalds/linux

C_TEST_FILES = {"file1.c": """
// SPDX-License-Identifier: GPL-2.0-or-later
/* 
 * Cryptographic API.
 *
 * TEA, XTEA, and XETA crypto alogrithms
 *
 * The TEA and Xtended TEA algorithms were developed by David Wheeler 
 * and Roger Needham at the Computer Laboratory of Cambridge University.
 *
 * Due to the order of evaluation in XTEA many people have incorrectly
 * implemented it.  XETA (XTEA in the wrong order), exists for
 * compatibility with these implementations.
 *
 * Copyright (c) 2004 Aaron Grothe ajgrothe@yahoo.com
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/mm.h>
#include <asm/byteorder.h>
#include <linux/crypto.h>
#include <linux/types.h>

#define TEA_KEY_SIZE		16
#define TEA_BLOCK_SIZE		8
#define TEA_ROUNDS		32
#define TEA_DELTA		0x9e3779b9

#define XTEA_KEY_SIZE		16
#define XTEA_BLOCK_SIZE		8
#define XTEA_ROUNDS		32
#define XTEA_DELTA		0x9e3779b9

struct tea_ctx {
	u32 KEY[4];
};

struct xtea_ctx {
	u32 KEY[4];
};

static int tea_setkey(struct crypto_tfm *tfm, const u8 *in_key,
		      unsigned int key_len)
{
	struct tea_ctx *ctx = crypto_tfm_ctx(tfm);
	const __le32 *key = (const __le32 *)in_key;

	ctx->KEY[0] = le32_to_cpu(key[0]);
	ctx->KEY[1] = le32_to_cpu(key[1]);
	ctx->KEY[2] = le32_to_cpu(key[2]);
	ctx->KEY[3] = le32_to_cpu(key[3]);

	return 0; 

}

static void tea_encrypt(struct crypto_tfm *tfm, u8 *dst, const u8 *src)
{
	u32 y, z, n, sum = 0;
	u32 k0, k1, k2, k3;
	struct tea_ctx *ctx = crypto_tfm_ctx(tfm);
	const __le32 *in = (const __le32 *)src;
	__le32 *out = (__le32 *)dst;

	y = le32_to_cpu(in[0]);
	z = le32_to_cpu(in[1]);

	k0 = ctx->KEY[0];
	k1 = ctx->KEY[1];
	k2 = ctx->KEY[2];
	k3 = ctx->KEY[3];

	n = TEA_ROUNDS;

	while (n-- > 0) {
		sum += TEA_DELTA;
		y += ((z << 4) + k0) ^ (z + sum) ^ ((z >> 5) + k1);
		z += ((y << 4) + k2) ^ (y + sum) ^ ((y >> 5) + k3);
	}
	
	out[0] = cpu_to_le32(y);
	out[1] = cpu_to_le32(z);
}

static void tea_decrypt(struct crypto_tfm *tfm, u8 *dst, const u8 *src)
{
	u32 y, z, n, sum;
	u32 k0, k1, k2, k3;
	struct tea_ctx *ctx = crypto_tfm_ctx(tfm);
	const __le32 *in = (const __le32 *)src;
	__le32 *out = (__le32 *)dst;

	y = le32_to_cpu(in[0]);
	z = le32_to_cpu(in[1]);

	k0 = ctx->KEY[0];
	k1 = ctx->KEY[1];
	k2 = ctx->KEY[2];
	k3 = ctx->KEY[3];

	sum = TEA_DELTA << 5;

	n = TEA_ROUNDS;

	while (n-- > 0) {
		z -= ((y << 4) + k2) ^ (y + sum) ^ ((y >> 5) + k3);
		y -= ((z << 4) + k0) ^ (z + sum) ^ ((z >> 5) + k1);
		sum -= TEA_DELTA;
	}
	
	out[0] = cpu_to_le32(y);
	out[1] = cpu_to_le32(z);
}

static int xtea_setkey(struct crypto_tfm *tfm, const u8 *in_key,
		       unsigned int key_len)
{
	struct xtea_ctx *ctx = crypto_tfm_ctx(tfm);
	const __le32 *key = (const __le32 *)in_key;

	ctx->KEY[0] = le32_to_cpu(key[0]);
	ctx->KEY[1] = le32_to_cpu(key[1]);
	ctx->KEY[2] = le32_to_cpu(key[2]);
	ctx->KEY[3] = le32_to_cpu(key[3]);

	return 0; 

}

static void xtea_encrypt(struct crypto_tfm *tfm, u8 *dst, const u8 *src)
{
	u32 y, z, sum = 0;
	u32 limit = XTEA_DELTA * XTEA_ROUNDS;
	struct xtea_ctx *ctx = crypto_tfm_ctx(tfm);
	const __le32 *in = (const __le32 *)src;
	__le32 *out = (__le32 *)dst;

	y = le32_to_cpu(in[0]);
	z = le32_to_cpu(in[1]);

	while (sum != limit) {
		y += ((z << 4 ^ z >> 5) + z) ^ (sum + ctx->KEY[sum&3]); 
		sum += XTEA_DELTA;
		z += ((y << 4 ^ y >> 5) + y) ^ (sum + ctx->KEY[sum>>11 &3]); 
	}
	
	out[0] = cpu_to_le32(y);
	out[1] = cpu_to_le32(z);
}

static void xtea_decrypt(struct crypto_tfm *tfm, u8 *dst, const u8 *src)
{
	u32 y, z, sum;
	struct tea_ctx *ctx = crypto_tfm_ctx(tfm);
	const __le32 *in = (const __le32 *)src;
	__le32 *out = (__le32 *)dst;

	y = le32_to_cpu(in[0]);
	z = le32_to_cpu(in[1]);

	sum = XTEA_DELTA * XTEA_ROUNDS;

	while (sum) {
		z -= ((y << 4 ^ y >> 5) + y) ^ (sum + ctx->KEY[sum>>11 & 3]);
		sum -= XTEA_DELTA;
		y -= ((z << 4 ^ z >> 5) + z) ^ (sum + ctx->KEY[sum & 3]);
	}
	
	out[0] = cpu_to_le32(y);
	out[1] = cpu_to_le32(z);
}


static void xeta_encrypt(struct crypto_tfm *tfm, u8 *dst, const u8 *src)
{
	u32 y, z, sum = 0;
	u32 limit = XTEA_DELTA * XTEA_ROUNDS;
	struct xtea_ctx *ctx = crypto_tfm_ctx(tfm);
	const __le32 *in = (const __le32 *)src;
	__le32 *out = (__le32 *)dst;

	y = le32_to_cpu(in[0]);
	z = le32_to_cpu(in[1]);

	while (sum != limit) {
		y += (z << 4 ^ z >> 5) + (z ^ sum) + ctx->KEY[sum&3];
		sum += XTEA_DELTA;
		z += (y << 4 ^ y >> 5) + (y ^ sum) + ctx->KEY[sum>>11 &3];
	}
	
	out[0] = cpu_to_le32(y);
	out[1] = cpu_to_le32(z);
}

static void xeta_decrypt(struct crypto_tfm *tfm, u8 *dst, const u8 *src)
{
	u32 y, z, sum;
	struct tea_ctx *ctx = crypto_tfm_ctx(tfm);
	const __le32 *in = (const __le32 *)src;
	__le32 *out = (__le32 *)dst;

	y = le32_to_cpu(in[0]);
	z = le32_to_cpu(in[1]);

	sum = XTEA_DELTA * XTEA_ROUNDS;

	while (sum) {
		z -= (y << 4 ^ y >> 5) + (y ^ sum) + ctx->KEY[sum>>11 & 3];
		sum -= XTEA_DELTA;
		y -= (z << 4 ^ z >> 5) + (z ^ sum) + ctx->KEY[sum & 3];
	}
	
	out[0] = cpu_to_le32(y);
	out[1] = cpu_to_le32(z);
}

static struct crypto_alg tea_algs[3] = { {
	.cra_name		=	"tea",
	.cra_driver_name	=	"tea-generic",
	.cra_flags		=	CRYPTO_ALG_TYPE_CIPHER,
	.cra_blocksize		=	TEA_BLOCK_SIZE,
	.cra_ctxsize		=	sizeof (struct tea_ctx),
	.cra_alignmask		=	3,
	.cra_module		=	THIS_MODULE,
	.cra_u			=	{ .cipher = {
	.cia_min_keysize	=	TEA_KEY_SIZE,
	.cia_max_keysize	=	TEA_KEY_SIZE,
	.cia_setkey		= 	tea_setkey,
	.cia_encrypt		=	tea_encrypt,
	.cia_decrypt		=	tea_decrypt } }
}, {
	.cra_name		=	"xtea",
	.cra_driver_name	=	"xtea-generic",
	.cra_flags		=	CRYPTO_ALG_TYPE_CIPHER,
	.cra_blocksize		=	XTEA_BLOCK_SIZE,
	.cra_ctxsize		=	sizeof (struct xtea_ctx),
	.cra_alignmask		=	3,
	.cra_module		=	THIS_MODULE,
	.cra_u			=	{ .cipher = {
	.cia_min_keysize	=	XTEA_KEY_SIZE,
	.cia_max_keysize	=	XTEA_KEY_SIZE,
	.cia_setkey		= 	xtea_setkey,
	.cia_encrypt		=	xtea_encrypt,
	.cia_decrypt		=	xtea_decrypt } }
}, {
	.cra_name		=	"xeta",
	.cra_driver_name	=	"xeta-generic",
	.cra_flags		=	CRYPTO_ALG_TYPE_CIPHER,
	.cra_blocksize		=	XTEA_BLOCK_SIZE,
	.cra_ctxsize		=	sizeof (struct xtea_ctx),
	.cra_alignmask		=	3,
	.cra_module		=	THIS_MODULE,
	.cra_u			=	{ .cipher = {
	.cia_min_keysize	=	XTEA_KEY_SIZE,
	.cia_max_keysize	=	XTEA_KEY_SIZE,
	.cia_setkey		= 	xtea_setkey,
	.cia_encrypt		=	xeta_encrypt,
	.cia_decrypt		=	xeta_decrypt } }
} };

static int __init tea_mod_init(void)
{
	return crypto_register_algs(tea_algs, ARRAY_SIZE(tea_algs));
}

static void __exit tea_mod_fini(void)
{
	crypto_unregister_algs(tea_algs, ARRAY_SIZE(tea_algs));
}

MODULE_ALIAS_CRYPTO("tea");
MODULE_ALIAS_CRYPTO("xtea");
MODULE_ALIAS_CRYPTO("xeta");

subsys_initcall(tea_mod_init);
module_exit(tea_mod_fini);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("TEA, XTEA & XETA Cryptographic Algorithms");
""",
                "file2.c": """
// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * xor.c : Multiple Devices driver for Linux
 *
 * Copyright (C) 1996, 1997, 1998, 1999, 2000,
 * Ingo Molnar, Matti Aarnio, Jakub Jelinek, Richard Henderson.
 *
 * Dispatch optimized RAID-5 checksumming functions.
 */

#define BH_TRACE 0
#include <linux/module.h>
#include <linux/gfp.h>
#include <linux/raid/xor.h>
#include <linux/jiffies.h>
#include <linux/preempt.h>
#include <asm/xor.h>

#ifndef XOR_SELECT_TEMPLATE
#define XOR_SELECT_TEMPLATE(x) (x)
#endif

/* The xor routines to use.  */
static struct xor_block_template *active_template;

void
xor_blocks(unsigned int src_count, unsigned int bytes, void *dest, void **srcs)
{
	unsigned long *p1, *p2, *p3, *p4;

	p1 = (unsigned long *) srcs[0];
	if (src_count == 1) {
		active_template->do_2(bytes, dest, p1);
		return;
	}

	p2 = (unsigned long *) srcs[1];
	if (src_count == 2) {
		active_template->do_3(bytes, dest, p1, p2);
		return;
	}

	p3 = (unsigned long *) srcs[2];
	if (src_count == 3) {
		active_template->do_4(bytes, dest, p1, p2, p3);
		return;
	}

	p4 = (unsigned long *) srcs[3];
	active_template->do_5(bytes, dest, p1, p2, p3, p4);
}
EXPORT_SYMBOL(xor_blocks);

/* Set of all registered templates.  */
static struct xor_block_template *__initdata template_list;

#define BENCH_SIZE (PAGE_SIZE)

static void __init
do_xor_speed(struct xor_block_template *tmpl, void *b1, void *b2)
{
	int speed;
	unsigned long now, j;
	int i, count, max;

	tmpl->next = template_list;
	template_list = tmpl;

	preempt_disable();

	/*
	 * Count the number of XORs done during a whole jiffy, and use
	 * this to calculate the speed of checksumming.  We use a 2-page
	 * allocation to have guaranteed color L1-cache layout.
	 */
	max = 0;
	for (i = 0; i < 5; i++) {
		j = jiffies;
		count = 0;
		while ((now = jiffies) == j)
			cpu_relax();
		while (time_before(jiffies, now + 1)) {
			mb(); /* prevent loop optimzation */
			tmpl->do_2(BENCH_SIZE, b1, b2);
			mb();
			count++;
			mb();
		}
		if (count > max)
			max = count;
	}

	preempt_enable();

	speed = max * (HZ * BENCH_SIZE / 1024);
	tmpl->speed = speed;

	printk(KERN_INFO "   %-10s: %5d.%03d MB/sec\n", tmpl->name,
	       speed / 1000, speed % 1000);
}

static int __init
calibrate_xor_blocks(void)
{
	void *b1, *b2;
	struct xor_block_template *f, *fastest;

	fastest = XOR_SELECT_TEMPLATE(NULL);

	if (fastest) {
		printk(KERN_INFO "xor: automatically using best "
				 "checksumming function   %-10s\n",
		       fastest->name);
		goto out;
	}

	b1 = (void *) __get_free_pages(GFP_KERNEL, 2);
	if (!b1) {
		printk(KERN_WARNING "xor: Yikes!  No memory available.\n");
		return -ENOMEM;
	}
	b2 = b1 + 2*PAGE_SIZE + BENCH_SIZE;

	/*
	 * If this arch/cpu has a short-circuited selection, don't loop through
	 * all the possible functions, just test the best one
	 */

#define xor_speed(templ)	do_xor_speed((templ), b1, b2)

	printk(KERN_INFO "xor: measuring software checksum speed\n");
	XOR_TRY_TEMPLATES;
	fastest = template_list;
	for (f = fastest; f; f = f->next)
		if (f->speed > fastest->speed)
			fastest = f;

	printk(KERN_INFO "xor: using function: %s (%d.%03d MB/sec)\n",
	       fastest->name, fastest->speed / 1000, fastest->speed % 1000);

#undef xor_speed

	free_pages((unsigned long)b1, 2);
out:
	active_template = fastest;
	return 0;
}

static __exit void xor_exit(void) { }

MODULE_LICENSE("GPL");

/* when built-in xor.o must initialize before drivers/md/md.o */
core_initcall(calibrate_xor_blocks);
module_exit(xor_exit);
"""}
