/*
 * See LICENSE for licensing information
 */

#ifndef SHD_TGEN_POOL_H_
#define SHD_TGEN_POOL_H_

#include <glib.h>

typedef struct _TGenPool TGenPool;

TGenPool* tgenpool_new(GDestroyNotify valueDestroyFunc);
void tgenpool_ref(TGenPool* pool);
void tgenpool_unref(TGenPool* pool);

void tgenpool_add(TGenPool* pool, gpointer item);
gpointer tgenpool_getRandom(TGenPool* pool);
gpointer tgenpool_getIndex(TGenPool* pool, const gint position);

#endif /* SHD_TGEN_POOL_H_ */
