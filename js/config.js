/*
 * ─────────────────────────────────────────────────────────────
 *  EVENT CONFIGURATION — the only file you need to edit.
 * ─────────────────────────────────────────────────────────────
 *  Leave a field as "" when you don't have it yet: the page hides
 *  whatever depends on it (map buttons, RSVP, music) instead of
 *  showing made-up information.
 *
 *  Items marked  TODO  still need your input before you share the link.
 */
window.INVITATION_CONFIG = {
  couple: {
    // Order as the couple asked: Muhammed first, then Waad.
    first: "Muhammed",
    second: "Waad",
    initials: "W & M",
  },

  event: {
    title: "Engagement Celebration",
    // Local date and time of the event, exactly as printed on the invitation:
    // Thursday, 5 November 2026 at 6:00 PM.
    start: "2026-11-05T18:00",
    durationHours: 4, // TODO: used for calendar entries and the "thank you" state

    // IANA time zone of the venue. The countdown, calendar entries and the
    // "your time" note for guests abroad are all computed in Cairo time.
    timeZone: "Africa/Cairo",
  },

  venue: {
    name: "Farha VIP Hall",
    address: "",  // not provided — the Maps link below is the source of truth
    // Google Maps share link supplied by the couple; every map/directions button uses it.
    mapsUrl: "https://maps.app.goo.gl/4AvzZR6PToQfZ1nH9?g_st=aw",
    // Optional: coordinates give the most precise directions, e.g. "30.0444,31.2357"
    coordinates: "",
    // Optional venue photograph, e.g. "assets/venue.webp"
    photo: "",
  },

  rsvp: {
    // Guests can reply via WhatsApp. International format, digits only, e.g. "201001234567".
    whatsapp: "", // TODO
    // …or via a form (Google Forms, Tally, etc.). Used when `whatsapp` is empty.
    url: "",
    deadline: "", // optional text, e.g. "25 October"
  },

  music: {
    // "زفة بمقدمة ام كلثوم" — a URL-safe copy of the file supplied in assets/.
    // It never plays until a guest taps "Tap to Listen" (or the music button),
    // and the stage scene performs only while it plays. Leave "" for no music.
    src: "assets/music/zaffa-om-kalthoum.mp3",
    title: "زفة بمقدمة ام كلثوم",
    startAt: 0,         // seconds into the track where the performance should begin
    loop: true,         // true: loop back to `startAt`; false: the scene bows out when the song ends
    bpm: 0,             // optional tempo, used for the halo's pulse when live audio analysis isn't available
    startOnOpen: false, // true: also start the song when the guest opens the doors
  },

  message: {
    // A well-known prayer for a couple (“May Allah bless you both, shower His
    // blessings upon you, and unite you in goodness”). Replace freely.
    arabic: "بارك الله لكما وبارك عليكما وجمع بينكما في خير",
    english:
      "With hearts full of gratitude, and by the will of Allah, we would be honoured to have you with us as we celebrate the beginning of our forever.",
    closing: "We can't wait to celebrate with you",
  },

  share: {
    title: "Muhammed & Waad — Engagement Celebration",
    text: "You're invited to our engagement celebration on Thursday, 5 November.",
  },
};
