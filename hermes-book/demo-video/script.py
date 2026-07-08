from manim import *

# ── Color Palette: warm academic / book theme ──
BG = "#2D2B55"
PAGE_BG = "#f9f6ef"
PAGE_TEXT = "#1a1a1a"
DARK_BG = "#1a1a1a"
DARK_TEXT = "#ccc"
ACCENT = "#c4782a"
SECONDARY = "#58C4DD"
HIGHLIGHT = "#FFFF00"
MONO = "Courier New"
SERIF = "Georgia"

# ── Book chapter titles ──
CHAPTERS = [
    "What is Hermes Agent?",
    "Installation & Setup",
    "The CLI Interface",
    "Tools & Capabilities",
    "The Skills System",
    "Memory & User Profiles",
    "Kanban & Task Management",
    "Cron Jobs & Automation",
    "Gateway & Multi-Platform",
    "SRE Monitoring with Hermes",
    "Automated Trading with Hermes",
    "Personal Automation",
    "Multi-Agent Workflows",
    "Advanced Configuration",
    "Top 20 Community Use Cases",
]


class Scene1_Title_Book(Scene):
    """Book cover / title reveal"""
    def construct(self):
        self.camera.background_color = BG

        # Decorative line
        line_top = Line(LEFT * 4, RIGHT * 4, color=ACCENT, stroke_width=1.5)

        # Book icon (a simple square with spine)
        book = Rectangle(width=2.2, height=2.8, color=ACCENT, fill_opacity=0.1, stroke_width=2)
        spine = Line(book.get_left(), book.get_left() + DOWN * 0.5, color=ACCENT, stroke_width=3)
        spine.shift(RIGHT * 0.1)
        pages = VGroup()
        for i in range(3):
            p = Rectangle(width=1.8, height=2.4, color=ACCENT, fill_opacity=0.05, stroke_width=1)
            p.shift(LEFT * i * 0.06 + UP * i * 0.03)
            pages.add(p)
        pages.move_to(book.get_center())
        book_group = VGroup(book, pages, spine)

        # Title text
        title = Text("Hermes Agent", font_size=48, color=ACCENT, weight=BOLD, font=MONO)
        subtitle = Text("The Complete Guide", font_size=28, color=PAGE_BG, font=MONO)
        subtitle.next_to(title, DOWN, buff=0.3)

        VGroup(title, subtitle).next_to(book_group, DOWN, buff=0.5)

        # URL
        url = Text("htmlpreview.github.io/...", font_size=16, color="#888", font=MONO)
        url.next_to(subtitle, DOWN, buff=0.4)

        all_elems = VGroup(book_group, title, subtitle, url)

        # Animate
        self.play(Write(line_top), run_time=0.5)
        self.play(FadeIn(book_group, scale=0.8), run_time=1.5)
        self.wait(0.3)
        self.play(Write(title), run_time=1.0)
        self.play(Write(subtitle), run_time=0.8)
        self.play(Write(url), run_time=0.6)
        self.wait(1.5)

        # Zoom to url and highlight
        url_highlight = SurroundingRectangle(url, color=ACCENT, buff=0.1, stroke_width=1.5)
        self.play(Create(url_highlight), run_time=0.5)
        self.wait(0.8)
        self.play(FadeOut(url_highlight), run_time=0.3)

        # Transition: fade everything
        self.play(FadeOut(VGroup(line_top, book_group, title, subtitle, url)), run_time=0.5)


class Scene2_Open_Book(Scene):
    """Opening the book — URL being accessed and book appears"""
    def construct(self):
        self.camera.background_color = BG

        # Background book pages (book interior)
        page_width = 8
        page_height = 4.5
        left_page = Rectangle(width=page_width / 2 + 0.1, height=page_height, color=ACCENT,
                              fill_opacity=0.0, stroke_width=1)
        right_page = Rectangle(width=page_width / 2 + 0.1, height=page_height, color=ACCENT,
                               fill_opacity=0.0, stroke_width=1)
        left_page.shift(LEFT * page_width / 4)
        right_page.shift(RIGHT * page_width / 4)

        spine = Line(ORIGIN, DOWN * page_height, color=ACCENT, stroke_width=2)
        spine.shift(UP * page_height / 2)

        pages = VGroup(left_page, right_page, spine)

        # Chapter header on right page
        ch_title = Text("1. What is Hermes Agent?", font_size=18, color=ACCENT, font=MONO, weight=BOLD)
        ch_title.move_to(right_page.get_center() + UP * 1.5)
        ch_title.scale_to_fit_width(right_page.width * 0.85)

        # Content text
        content_lines = [
            "Hermes Agent is an open-source agentic AI",
            "framework by Nous Research. Unlike a",
            "standard chatbot, Hermes is a long-running,",
            "tool-using AI agent that lives on your",
            "machine. It has tools, memory, a task",
            "board, a scheduler, and can spawn",
            "sub-agents.",
        ]
        lines = VGroup()
        for i, line in enumerate(content_lines):
            t = Text(line, font_size=11, color=PAGE_TEXT, font=MONO)
            t.move_to(right_page.get_center() + DOWN * 0.2 + DOWN * i * 0.4)
            t.scale_to_fit_width(right_page.width * 0.85)
            lines.add(t)

        # Bullet points on left page
        bullet_lines = [
            "Agent-first, not chat-first",
            "Local and sovereign data",
            "Extensible by design",
        ]
        bullets = VGroup()
        for i, line in enumerate(bullet_lines):
            t = Text(f"   {line}", font_size=11, color=PAGE_TEXT, font=MONO)
            t.move_to(left_page.get_center() + UP * 0.5 + DOWN * i * 0.5)
            t.scale_to_fit_width(left_page.width * 0.8)
            bullets.add(t)

        page_num = Text("1", font_size=10, color="#999", font=MONO)
        page_num.move_to(right_page.get_bottom() + UP * 0.3 + RIGHT * 0.3)

        content = VGroup(ch_title, lines, bullets, page_num)

        # Page turn animation
        self.play(FadeIn(pages, scale=0.95, run_time=1.0))
        self.wait(0.2)

        # Reveal content by writing it
        self.play(Write(ch_title), run_time=0.6)
        self.play(LaggedStart(*[Write(l) for l in lines], lag_ratio=0.1), run_time=0.8)
        self.play(LaggedStart(*[Write(b) for b in bullets], lag_ratio=0.1), run_time=0.5)
        self.play(Write(page_num), run_time=0.3)
        self.wait(1.5)

        # Highlights
        for w in ["open-source", "tool-using", "memory", "sub-agents"]:
            self.play(FadeToColor(ch_title, HIGHLIGHT), run_time=0.15)
            self.play(FadeToColor(ch_title, ACCENT), run_time=0.15)

        self.wait(1.0)


class Scene3_TOC_Sidebar(Scene):
    """Table of Contents slides out"""
    def construct(self):
        self.camera.background_color = BG

        # The book pages (dimmed in background)
        page_width = 8
        page_height = 4.5
        left_page = Rectangle(width=page_width / 2, height=page_height, color=ACCENT,
                              fill_opacity=0.0, stroke_width=0.5)
        right_page = Rectangle(width=page_width / 2, height=page_height, color=ACCENT,
                               fill_opacity=0.0, stroke_width=0.5)
        left_page.shift(LEFT * page_width / 4)
        right_page.shift(RIGHT * page_width / 4)
        spine = Line(ORIGIN, DOWN * page_height, color=ACCENT, stroke_width=1)
        spine.shift(UP * page_height / 2)
        pages = VGroup(left_page, right_page, spine)
        pages.scale(0.6).shift(RIGHT * 0.5)

        self.add(pages)

        # TOC panel slides in from left
        toc_bg = Rectangle(width=3.0, height=4.8, color=PAGE_BG, fill_opacity=0.92,
                           stroke_width=1, stroke_color=ACCENT)
        toc_bg.shift(LEFT * 3.5)

        toc_title = Text("Contents", font_size=16, color=ACCENT, font=MONO, weight=BOLD)
        toc_title.next_to(toc_bg.get_top(), DOWN, buff=0.3)
        toc_title.shift(LEFT * 3.5)

        # Show chapters with highlights
        toc_items = VGroup()
        for i, ch in enumerate(CHAPTERS[:10]):
            num = f"{i+1}."
            t = Text(f"{num} {ch}", font_size=9, color=PAGE_TEXT, font=MONO)
            t.move_to(toc_bg.get_center() + UP * 1.8 + DOWN * i * 0.38)
            t.shift(LEFT * 3.5)
            toc_items.add(t)

        item_highlight = SurroundingRectangle(toc_items[0], color=ACCENT, buff=0.05, stroke_width=1)

        # Animate TOC sliding in
        self.play(FadeIn(toc_bg, shift=LEFT * 0.5), run_time=0.6)
        self.play(Write(toc_title), run_time=0.3)
        self.play(LaggedStart(*[Write(item) for item in toc_items], lag_ratio=0.03), run_time=1.2)
        self.wait(0.3)

        # Highlight current chapter
        self.play(Create(item_highlight), run_time=0.3)
        self.wait(0.5)

        # Scroll down a bit
        self.play(toc_items.animate.shift(UP * 0.3), run_time=0.5)
        self.wait(0.3)

        # TOC slides back out
        self.play(FadeOut(toc_bg, shift=LEFT * 0.5),
                  FadeOut(toc_title),
                  FadeOut(toc_items),
                  FadeOut(item_highlight),
                  FadeOut(pages),
                  run_time=0.5)


class Scene4_Page_Nav(Scene):
    """Page navigation - flipping to a different chapter"""
    def construct(self):
        self.camera.background_color = BG

        # Right page - Chapter 5
        page = Rectangle(width=4.5, height=3.8, color=ACCENT,
                         fill_opacity=0.0, stroke_width=1)
        page.shift(RIGHT * 0.5)

        ch_title = Text("5. The Skills System", font_size=16, color=ACCENT, font=MONO, weight=BOLD)
        ch_title.move_to(page.get_center() + UP * 1.3)

        content_lines = [
            "Skills are procedural memory - reusable",
            "knowledge teaching the agent specific",
            "tasks. Loaded with skill_view(), created",
            "with skill_manage(). YAML frontmatter +",
            "markdown body. The Curator auto-prunes",
            "unused skills after 30 days.",
        ]
        lines = VGroup()
        for i, line in enumerate(content_lines):
            t = Text(line, font_size=10, color=PAGE_TEXT, font=MONO)
            t.move_to(page.get_center() + DOWN * 0.2 + DOWN * i * 0.35)
            lines.add(t)

        page_num = Text("42", font_size=10, color="#999", font=MONO)
        page_num.move_to(page.get_bottom() + UP * 0.25 + RIGHT * 0.3)

        VGroup(ch_title, lines, page_num)

        # Prev/Next nav buttons
        prev_btn = Square(side_length=0.5, color=ACCENT, fill_opacity=0.1, stroke_width=1)
        prev_btn.shift(LEFT * 4.5)
        prev_label = Text("<", font_size=18, color=ACCENT, font=MONO)
        prev_label.move_to(prev_btn.get_center())

        next_btn = Square(side_length=0.5, color=ACCENT, fill_opacity=0.2, stroke_width=1.5)
        next_btn.shift(RIGHT * 3.5)
        next_label = Text(">", font_size=18, color=ACCENT, font=MONO)
        next_label.move_to(next_btn.get_center())

        # Progress bar at bottom
        progress_bg = Line(LEFT * 3.5, RIGHT * 3.5, color="#555", stroke_width=1)
        progress_bg.shift(DOWN * 2.8)
        progress_fill = Line(LEFT * 3.5, RIGHT * 1.8, color=ACCENT, stroke_width=1.5)
        progress_fill.shift(DOWN * 2.8)
        progress_text = Text("Chapter 5 of 15", font_size=8, color="#888", font=MONO)
        progress_text.next_to(progress_bg, UP, buff=0.1)

        # Animate
        self.play(FadeIn(page, scale=0.9), run_time=0.5)
        self.play(Write(ch_title), run_time=0.4)
        self.play(LaggedStart(*[Write(l) for l in lines], lag_ratio=0.08), run_time=0.8)
        self.play(Write(page_num), run_time=0.2)

        # Show nav
        self.play(FadeIn(prev_btn), FadeIn(prev_label), run_time=0.3)
        self.play(FadeIn(next_btn), FadeIn(next_label), run_time=0.3)
        self.play(Write(progress_bg), Write(progress_fill), Write(progress_text), run_time=0.4)

        self.wait(0.5)

        # Click next → page flips to Chapter 6
        flip_highlight = SurroundingRectangle(next_btn, color=HIGHLIGHT, buff=0.05, stroke_width=2)
        self.play(Create(flip_highlight), run_time=0.2)
        self.wait(0.2)

        # Page turn animation
        new_ch = Text("6. Memory & User Profiles", font_size=16, color=ACCENT, font=MONO, weight=BOLD)
        new_ch.move_to(page.get_center() + UP * 1.3)
        new_lines_text = [
            "Memory stores persistent facts across",
            "sessions via MEMORY.md and USER.md.",
            "Injected every turn. Compact, focused",
            "on user preferences. Session search",
            "recovers past conversations via FTS5.",
        ]
        new_lines = VGroup()
        for i, line in enumerate(new_lines_text):
            t = Text(line, font_size=10, color=PAGE_TEXT, font=MONO)
            t.move_to(page.get_center() + DOWN * 0.2 + DOWN * i * 0.35)
            new_lines.add(t)
        new_page_num = Text("48", font_size=10, color="#999", font=MONO)
        new_page_num.move_to(page.get_bottom() + UP * 0.25 + RIGHT * 0.3)

        # Progress bar advance
        new_pf = Line(LEFT * 3.5, RIGHT * 2.2, color=ACCENT, stroke_width=1.5)
        new_pf.shift(DOWN * 2.8)
        new_pt = Text("Chapter 6 of 15", font_size=8, color="#888", font=MONO)
        new_pt.next_to(new_pf, UP, buff=0.1)

        # Fade old, fade in new (simulating page flip)
        self.play(FadeOut(ch_title), FadeOut(lines), FadeOut(page_num),
                  FadeOut(progress_text), FadeOut(progress_fill),
                  run_time=0.15)
        self.play(page.animate.shift(LEFT * 0.05).scale(0.98), run_time=0.1)
        self.play(page.animate.shift(RIGHT * 0.05).scale(1.02), run_time=0.1)
        self.play(Write(new_ch), Write(new_lines), Write(new_page_num),
                  Write(new_pf), Write(new_pt),
                  Transform(progress_fill, new_pf),
                  Transform(progress_text, new_pt),
                  run_time=0.6)

        self.play(FadeOut(flip_highlight), run_time=0.2)
        self.wait(1.0)


class Scene5_Dark_Mode(Scene):
    """Toggle between light and dark themes"""
    def construct(self):
        self.camera.background_color = PAGE_BG
        # Initially show light mode

        # A single page
        page = Rectangle(width=5, height=3.5, color="#ddd", fill_opacity=0.0,
                         stroke_width=1, stroke_color="#bbb")

        ch_title = Text("14. Advanced Configuration", font_size=15, color="#c4782a",
                        font=MONO, weight=BOLD)
        ch_title.move_to(page.get_center() + UP * 1.2)

        text_color = "#1a1a1a"
        lines_text = [
            "config.yaml: model, agent, terminal,",
            "gateway settings. Profiles isolate",
            "configs. Custom providers via",
            "custom:name. Plugins extend",
            "functionality.",
        ]
        lines = VGroup()
        for i, line in enumerate(lines_text):
            t = Text(line, font_size=10, color=text_color, font=MONO)
            t.move_to(page.get_center() + DOWN * 0.2 + DOWN * i * 0.35)
            lines.add(t)

        # Sun button (toggle)
        btn = Circle(radius=0.3, color=ACCENT, fill_opacity=0.2, stroke_width=1.5)
        btn.shift(UP * 2.5 + RIGHT * 3.5)
        btn_label = Text("☀", font_size=14, color=ACCENT)
        btn_label.move_to(btn.get_center())

        label_text = Text("Dark Mode", font_size=8, color="#888", font=MONO)
        label_text.next_to(btn, DOWN, buff=0.1)

        # Assemble light mode
        light_group = VGroup(page, ch_title, lines, btn, btn_label, label_text)
        self.play(FadeIn(light_group), run_time=0.8)
        self.wait(1.0)

        # Highlight the button
        btn_glow = Circle(radius=0.35, color=HIGHLIGHT, fill_opacity=0.3, stroke_width=2)
        btn_glow.move_to(btn.get_center())
        self.play(Create(btn_glow), run_time=0.3)
        self.wait(0.3)

        # Transition to dark mode
        dark = VGroup()
        self.play(
            page.animate.set_stroke_color("#444"),
            ch_title.animate.set_color(ACCENT),
            lines.animate.set_color("#ccc"),
            btn.animate.set_fill("#333344", 0.3),
            btn_label.animate.set_color(HIGHLIGHT),
            btn_label.animate.become(Text("🌙", font_size=14).move_to(btn.get_center())),
            FadeOut(btn_glow),
            run_time=1.0
        )
        # Change background
        self.camera.background_color = DARK_BG
        self.wait(0.2)

        # Flash transition
        flash = FullScreenRectangle(color=DARK_BG, fill_opacity=0.0)
        self.play(flash.animate.set_opacity(0.99), run_time=0.15)
        self.play(flash.animate.set_opacity(0.0), run_time=0.15)

        self.wait(0.5)

        # Toggle back to light
        btn_glow2 = Circle(radius=0.35, color=HIGHLIGHT, fill_opacity=0.3, stroke_width=2)
        btn_glow2.move_to(btn.get_center())
        self.play(Create(btn_glow2), run_time=0.2)

        self.play(
            page.animate.set_stroke_color("#bbb"),
            ch_title.animate.set_color(ACCENT),
            lines.animate.set_color(PAGE_TEXT),
            btn.animate.set_fill(ACCENT, 0.2),
            btn_label.animate.become(Text("☀", font_size=14, color=ACCENT).move_to(btn.get_center())),
            FadeOut(btn_glow2),
            run_time=1.0
        )
        self.camera.background_color = PAGE_BG

        self.wait(1.0)


class Scene6_Font_Controls(Scene):
    """Font size adjustment controls"""
    def construct(self):
        self.camera.background_color = BG

        # Book page
        page = Rectangle(width=4.5, height=2.5, color=ACCENT,
                         fill_opacity=0.0, stroke_width=0.5)
        page.shift(UP * 0.3)

        sample = Text(
            "Hermes Agent connects an LLM\nto a rich set of tools through\na tool-use loop.",
            font_size=12, color=PAGE_BG, font=MONO
        )
        sample.move_to(page.get_center())

        # Font control panel at bottom
        panel = RoundedRectangle(width=2.0, height=0.6, color=ACCENT,
                                 fill_opacity=0.1, stroke_width=1)
        panel.shift(DOWN * 2.0)

        minus_btn = Square(side_length=0.35, color=ACCENT, fill_opacity=0.1, stroke_width=1)
        minus_btn.move_to(panel.get_left() + RIGHT * 0.4)
        minus_label = Text("A-", font_size=11, color=ACCENT, font=MONO)
        minus_label.move_to(minus_btn.get_center())

        plus_btn = Square(side_length=0.35, color=ACCENT, fill_opacity=0.2, stroke_width=1.5)
        plus_btn.move_to(panel.get_right() + LEFT * 0.4)
        plus_label = Text("A+", font_size=11, color=ACCENT, font=MONO)
        plus_label.move_to(plus_btn.get_center())

        current_size_text = Text("14px", font_size=9, color="#888", font=MONO)
        current_size_text.move_to(panel.get_center())

        # Label
        controls_label = Text("Aa  Font Size", font_size=8, color="#666", font=MONO)
        controls_label.next_to(panel, UP, buff=0.1)

        # Animate
        self.play(FadeIn(page), Write(sample), run_time=0.8)
        self.play(FadeIn(panel), FadeIn(minus_btn), FadeIn(plus_btn),
                  FadeIn(minus_label), FadeIn(plus_label),
                  Write(current_size_text), Write(controls_label),
                  run_time=0.6)

        self.wait(0.8)

        # Click A+ → size increases
        plus_highlight = SurroundingRectangle(plus_btn, color=HIGHLIGHT, buff=0.05, stroke_width=2)
        self.play(Create(plus_highlight), run_time=0.2)
        self.wait(0.2)

        new_sample = Text(
            "Hermes Agent connects an LLM\nto a rich set of tools through\na tool-use loop.",
            font_size=16, color=PAGE_BG, font=MONO
        )
        new_sample.move_to(page.get_center())
        new_size_text = Text("18px", font_size=9, color="#888", font=MONO)
        new_size_text.move_to(panel.get_center())

        self.play(Transform(sample, new_sample), Transform(current_size_text, new_size_text),
                  FadeOut(plus_highlight), run_time=0.6)
        self.wait(0.5)

        # Click A- → size decreases
        minus_highlight = SurroundingRectangle(minus_btn, color=ACCENT, buff=0.05, stroke_width=2)
        self.play(Create(minus_highlight), run_time=0.2)
        self.wait(0.2)

        new_sample2 = Text(
            "Hermes Agent connects an LLM\nto a rich set of tools through\na tool-use loop.",
            font_size=10, color=PAGE_BG, font=MONO
        )
        new_sample2.move_to(page.get_center())
        new_size_text2 = Text("12px", font_size=9, color="#888", font=MONO)
        new_size_text2.move_to(panel.get_center())

        self.play(Transform(sample, new_sample2), Transform(current_size_text, new_size_text2),
                  FadeOut(minus_highlight), run_time=0.6)
        self.wait(1.0)


class Scene7_URL_Outro(Scene):
    """Final scene - how to access the book"""
    def construct(self):
        self.camera.background_color = BG

        # "Access the Book" title
        title = Text("Access the Book", font_size=40, color=ACCENT, font=MONO, weight=BOLD)
        self.play(Write(title), run_time=1.0)
        self.wait(0.5)

        self.play(title.animate.shift(UP * 2), run_time=0.5)

        # Step 1: Open browser
        step1 = Text("1. Open your browser", font_size=18, color=PAGE_BG, font=MONO)
        step1.next_to(title, DOWN, buff=0.5)

        # URL
        url_text = Text(
            "htmlpreview.github.io/?github.com/\n"
            "decniner/HermesP1/blob/main/\n"
            "hermes-book/HermesAgentBook.html",
            font_size=14, color=ACCENT, font=MONO, t2c={
                "htmlpreview": ACCENT, "github.com": ACCENT,
            }
        )
        url_text.next_to(step1, DOWN, buff=0.4)

        url_box = SurroundingRectangle(url_text, color=ACCENT, buff=0.2, stroke_width=1,
                                       corner_radius=0.1)

        self.play(Write(step1), run_time=0.5)
        self.wait(0.3)
        self.play(Write(url_text), Create(url_box), run_time=1.0)
        self.wait(0.5)

        # Step 2: Navigate
        step2 = Text("2. Navigate using the menu & TOC", font_size=18, color=PAGE_BG, font=MONO)
        step2.next_to(url_box, DOWN, buff=0.5)
        self.play(Write(step2), run_time=0.5)
        self.wait(0.3)

        # Features list
        features_text = (
            "  15 chapters covering the entire ecosystem\n"
            "  Page-flip interface with smooth animation\n"
            "  Table of Contents sidebar\n"
            "  Dark mode & font size controls\n"
            "  Progress tracking\n"
        )
        features = Text(features_text, font_size=12, color="#888", font=MONO)
        features.next_to(step2, DOWN, buff=0.3)

        self.play(LaggedStart(*[Write(features[i*40:(i+1)*40]) for i in range(6)],
                               lag_ratio=0.1), run_time=1.5)
        self.wait(0.5)

        # Final CTA
        cta = Text("Explore →", font_size=28, color=HIGHLIGHT, font=MONO, weight=BOLD)
        cta.next_to(features, DOWN, buff=0.5)
        self.play(Write(cta), run_time=0.6)
        self.wait(0.8)

        # Pulse effect on CTA
        for _ in range(2):
            self.play(cta.animate.scale(1.08), run_time=0.3)
            self.play(cta.animate.scale(0.92), run_time=0.3)
        self.wait(0.5)
