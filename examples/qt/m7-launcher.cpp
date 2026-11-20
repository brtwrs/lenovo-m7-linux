// m7-launcher: starts a QML file on the Lenovo Tab M7 under cage/libhybris.
// 1. Requests a 24-bit colour buffer (qmlscene gets RGB565 on the M7 = banding).
// 2. Registers LiveVideo (import M7 1.0): an RTSP H.264 player. GStreamer decodes in software (avdec_h264)
//    to RGBx in an appsink; every frame becomes a plain texture, same path as an Image.
//    VIDEO ONLY on purpose: QtMultimedia/playbin also plays the audio track, and ALSA mmap playback
//    crashes this kernel (Oops in snd_pcm_mmap_data_fault).
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QSurfaceFormat>
#include <QUrl>
#include <QQuickItem>
#include <QQuickWindow>
#include <QSGSimpleTextureNode>
#include <QImage>
#include <QMutex>
#include <QMetaObject>
#include <QtQml>
#include <gst/gst.h>
#include <gst/app/gstappsink.h>

class LiveVideo : public QQuickItem {
    Q_OBJECT
    Q_PROPERTY(QString source READ source WRITE setSource NOTIFY bronChanged)
    Q_PROPERTY(int fps READ fps WRITE setFps NOTIFY fpsChanged)
    Q_PROPERTY(bool playing READ playing NOTIFY speeltChanged)
public:
    LiveVideo() { setFlag(ItemHasContents, true); }
    ~LiveVideo() override { stop(); }
    QString source() const { return m_bron; }
    int fps() const { return m_fps; }
    bool playing() const { return m_speelt; }
    void setSource(const QString &b) { if (b == m_bron) return; m_bron = b; emit bronChanged(); stop(); if (!b.isEmpty()) start(); }
    void setFps(int f) { if (f == m_fps) return; m_fps = f; emit fpsChanged(); }
signals:
    void bronChanged(); void fpsChanged(); void speeltChanged(); void error(QString text);
protected:
    QSGNode *updatePaintNode(QSGNode *old, UpdatePaintNodeData *) override {
        auto *n = static_cast<QSGSimpleTextureNode *>(old);
        QImage f;
        { QMutexLocker l(&m_lock); if (!m_new) { if (n) n->setRect(fillRect()); return n; } f = m_frame; m_new = false; }
        if (f.isNull()) return n;
        if (!n) { n = new QSGSimpleTextureNode(); n->setOwnsTexture(true); n->setFiltering(QSGTexture::Linear); }
        n->setTexture(window()->createTextureFromImage(f));   // the node deletes the old texture (ownsTexture)
        m_bw = f.width(); m_bh = f.height();
        n->setRect(fillRect());
        return n;
    }
private:
    QRectF fillRect() const {   // PreserveAspectCrop: fill the item, the overflow falls outside (clip in QML)
        if (!m_bw || !m_bh) return boundingRect();
        qreal s = qMax(width() / m_bw, height() / m_bh), w = m_bw * s, h = m_bh * s;
        return QRectF((width() - w) / 2, (height() - h) / 2, w, h);
    }
    static GstFlowReturn newFrame(GstAppSink *s, gpointer self) {
        auto *lb = static_cast<LiveVideo *>(self);
        GstSample *smp = gst_app_sink_pull_sample(s);
        if (!smp) return GST_FLOW_OK;
        GstCaps *caps = gst_sample_get_caps(smp);
        GstStructure *st = gst_caps_get_structure(caps, 0);
        int w = 0, h = 0; gst_structure_get_int(st, "width", &w); gst_structure_get_int(st, "height", &h);
        GstBuffer *buf = gst_sample_get_buffer(smp); GstMapInfo m;
        if (w && h && gst_buffer_map(buf, &m, GST_MAP_READ)) {
            QImage img(m.data, w, h, w * 4, QImage::Format_RGBX8888);
            { QMutexLocker l(&lb->m_lock); lb->m_frame = img.copy(); lb->m_new = true; }
            gst_buffer_unmap(buf, &m);
            QMetaObject::invokeMethod(lb, [lb] { if (!lb->m_speelt) { lb->m_speelt = true; emit lb->speeltChanged(); } lb->update(); }, Qt::QueuedConnection);
        }
        gst_sample_unref(smp);
        return GST_FLOW_OK;
    }
    static gboolean busMessage(GstBus *, GstMessage *msg, gpointer self) {
        auto *lb = static_cast<LiveVideo *>(self);
        if (GST_MESSAGE_TYPE(msg) == GST_MESSAGE_ERROR || GST_MESSAGE_TYPE(msg) == GST_MESSAGE_EOS) {
            GError *e = nullptr; gchar *d = nullptr;
            if (GST_MESSAGE_TYPE(msg) == GST_MESSAGE_ERROR) gst_message_parse_error(msg, &e, &d);
            QString t = e ? QString::fromUtf8(e->message) : QStringLiteral("end of stream");
            if (e) g_error_free(e); g_free(d);
            QMetaObject::invokeMethod(lb, [lb, t] { lb->stop(); emit lb->error(t); }, Qt::QueuedConnection);
        }
        return TRUE;
    }
    void start() {
        // never paste the address into the pipeline text (it could add elements): fixed pipeline,
        // location as a property, only rtsp(s):// without control characters; fps clamped
        if (!(m_bron.startsWith(QLatin1String("rtsp://")) || m_bron.startsWith(QLatin1String("rtsps://")))) { emit error(QStringLiteral("not an rtsp address")); return; }
        for (QChar c : m_bron) if (c.unicode() < 0x20 || c.unicode() == 0x7f) { emit error(QStringLiteral("invalid address")); return; }
        const int fps = qBound(1, m_fps, 30);
        QString p = QStringLiteral("rtspsrc name=source protocols=tcp latency=1000 ! rtph264depay ! h264parse ! avdec_h264 max-threads=2 "
                                   "! videorate drop-only=true ! video/x-raw,framerate=%1/1 ! videoconvert ! video/x-raw,format=RGBx "
                                   "! appsink name=s max-buffers=1 drop=true sync=false").arg(fps);
        GError *e = nullptr;
        m_pipe = gst_parse_launch(p.toUtf8().constData(), &e);
        if (!m_pipe) { emit error(e ? QString::fromUtf8(e->message) : QStringLiteral("pipeline")); if (e) g_error_free(e); return; }
        GstElement *source = gst_bin_get_by_name(GST_BIN(m_pipe), "source");
        g_object_set(source, "location", m_bron.toUtf8().constData(), nullptr);
        gst_object_unref(source);
        GstElement *s = gst_bin_get_by_name(GST_BIN(m_pipe), "s");
        GstAppSinkCallbacks cb = {}; cb.new_sample = &LiveVideo::newFrame;
        gst_app_sink_set_callbacks(GST_APP_SINK(s), &cb, this, nullptr);
        gst_object_unref(s);
        GstBus *bus = gst_element_get_bus(m_pipe); m_busId = gst_bus_add_watch(bus, &LiveVideo::busMessage, this); gst_object_unref(bus);
        gst_element_set_state(m_pipe, GST_STATE_PLAYING);
    }
    void stop() {
        if (m_pipe) { gst_element_set_state(m_pipe, GST_STATE_NULL); if (m_busId) g_source_remove(m_busId); m_busId = 0; gst_object_unref(m_pipe); m_pipe = nullptr; }
        if (m_speelt) { m_speelt = false; emit speeltChanged(); }
    }
    QString m_bron; int m_fps = 15; bool m_speelt = false;
    GstElement *m_pipe = nullptr; guint m_busId = 0;
    QMutex m_lock; QImage m_frame; bool m_new = false; int m_bw = 0, m_bh = 0;
};

int main(int argc, char **argv) {
    gst_init(&argc, &argv);
    QSurfaceFormat f;
    f.setRedBufferSize(8); f.setGreenBufferSize(8); f.setBlueBufferSize(8); f.setAlphaBufferSize(0);
    f.setDepthBufferSize(24); f.setStencilBufferSize(8);
    QSurfaceFormat::setDefaultFormat(f);
    QGuiApplication app(argc, argv);
    qmlRegisterType<LiveVideo>("M7", 1, 0, "LiveVideo");
    QQmlApplicationEngine engine;
    engine.load(QUrl::fromLocalFile(argc > 1 ? argv[1] : "/root/qml/main.qml"));
    if (engine.rootObjects().isEmpty()) return 1;
    return app.exec();
}
#include "m7-launcher.moc"
