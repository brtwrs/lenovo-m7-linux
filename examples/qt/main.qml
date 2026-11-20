// Minimal example for the M7: clock, fps counter, touch test, optional live RTSP background.
// Run with: /root/m7-linux/scripts/qt-start.sh /root/qml/main.qml
// Live video: put an rtsp:// URL (H.264) in /root/qml/stream.txt
import QtQuick 2.15
import QtQuick.Window 2.15
import M7 1.0

Window {
    id: win; visible: true; width: 1024; height: 600; color: "#121110"
    property int frames: 0
    property int fps: 0
    onFrameSwapped: frames++
    Timer { interval: 1000; running: true; repeat: true; onTriggered: { win.fps = win.frames; win.frames = 0 } }

    property string stream: ""
    Component.onCompleted: { var x = new XMLHttpRequest(); x.open("GET", "file:///root/qml/stream.txt")
        x.onreadystatechange = function () { if (x.readyState === XMLHttpRequest.DONE) win.stream = (x.responseText || "").trim() }; x.send() }
    LiveVideo { id: live; anchors.fill: parent; source: win.stream; fps: 15; visible: playing; onError: console.log("live: " + text) }
    Rectangle { anchors.fill: parent; color: "#000"; opacity: live.playing ? 0.3 : 0 }

    Text { x: 40; y: 20; color: "#f3eee6"; font.pixelSize: 120; font.weight: Font.Light; text: Qt.formatTime(new Date(), "hh:mm")
        Timer { interval: 1000; running: true; repeat: true; onTriggered: parent.text = Qt.formatTime(new Date(), "hh:mm") } }
    Text { x: 44; y: 170; color: "#8caa78"; font.pixelSize: 24; text: win.fps + " fps" + (live.playing ? " · live" : "") }

    // touch test: tap anywhere, a ring appears where you touched
    Rectangle { id: ring; width: 80; height: 80; radius: 40; color: "transparent"; border.color: "#d6a050"; border.width: 4; opacity: 0
        NumberAnimation on opacity { id: weg; from: 1; to: 0; duration: 800; running: false } }
    MouseArea { anchors.fill: parent; onPressed: { ring.x = mouse.x - 40; ring.y = mouse.y - 40; weg.restart() } }

    // a small animation, to see that it is smooth
    Rectangle { width: 60; height: 60; radius: 12; color: "#d6a050"; y: parent.height - 120
        SequentialAnimation on x { loops: Animation.Infinite
            NumberAnimation { from: 40; to: win.width - 100; duration: 2000; easing.type: Easing.InOutQuad }
            NumberAnimation { from: win.width - 100; to: 40; duration: 2000; easing.type: Easing.InOutQuad } } }
}
