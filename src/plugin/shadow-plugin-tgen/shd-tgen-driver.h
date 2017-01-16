/*
 * See LICENSE for licensing information
 */

#ifndef SHD_TGEN_DRIVER_H_
#define SHD_TGEN_DRIVER_H_

#include "shd-tgen.h"

/* opaque struct containing trafficgenerator data */
typedef struct _TGenDriver TGenDriver;
typedef struct _ForwardPeer ForwardPeer;

TGenDriver* tgendriver_new(TGenGraph* graph);
void tgendriver_ref(TGenDriver* driver);
void tgendriver_unref(TGenDriver* driver);

void tgendriver_activate(TGenDriver* driver);

gboolean tgendriver_hasEnded(TGenDriver* driver);
gint tgendriver_getEpollDescriptor(TGenDriver* driver);

// this is for processing servers to pick the server to forward the message to
TGenPool* tgendriver_getForwardPeer(TGenDriver* driver);


#endif /* SHD_TGEN_DRIVER_H_ */
