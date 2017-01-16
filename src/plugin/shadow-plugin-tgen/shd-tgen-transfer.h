/*
 * See LICENSE for licensing information
 */

#ifndef SHD_TGEN_TRANSFER_H_
#define SHD_TGEN_TRANSFER_H_

typedef enum _TGenTransferType {
    TGEN_TYPE_NONE, TGEN_TYPE_GET, TGEN_TYPE_PUT, TGEN_TYPE_FORWARD, TGEN_TYPE_FORWARD_SERVE, TGEN_TYPE_FORWARD_RETURN
} TGenTransferType;

typedef struct _TGenTransfer TGenTransfer;

typedef void (*TGenTransfer_notifyCompleteFunc)(gpointer data1, gpointer data2, gboolean wasSuccess);

TGenTransfer* tgentransfer_new(const gchar* idStr, gsize count, TGenTransferType type, TGenTransferType myType, gsize size, guint64 timeout, guint64 stallout,
        TGenTransport* transport, TGenTransfer_notifyCompleteFunc notify,
        gpointer data1, gpointer data2, GDestroyNotify destructData1, GDestroyNotify destructData2, gint64 sendRate);
void tgentransfer_ref(TGenTransfer* transfer);
void tgentransfer_unref(TGenTransfer* transfer);

TGenEvent tgentransfer_onEvent(TGenTransfer* transfer, gint descriptor, TGenEvent events);
gboolean tgentransfer_onCheckTimeout(TGenTransfer* transfer, gint descriptor);

#endif /* SHD_TGEN_TRANSFER_H_ */
