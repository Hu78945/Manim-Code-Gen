from manim import *


# Define a custom Shake animation class
class Shake(Animation):
    def __init__(self, mobject, amplitude=0.2, **kwargs):
        self.amplitude = amplitude
        super().__init__(mobject, **kwargs)
        
    def interpolate_mobject(self, alpha):
        # Original position
        org_center = self.starting_mobject.get_center()
        
        # Apply a sine wave for shaking effect
        # As alpha increases from 0 to 1, we complete multiple oscillations
        direction = RIGHT * self.amplitude * np.sin(alpha * TAU * 4)
        
        # Update the position
        self.mobject.move_to(org_center + direction)


class DeadlockScene(Scene):
    def construct(self):
        # Create a function for explanatory text
        def show_explanation(text_content, position=DOWN*3, color=WHITE):
            explanation = Text(text_content, color=color, font_size=24)
            explanation.move_to(position)
            self.play(FadeIn(explanation))
            return explanation
        
        # 1. Title
        title = Title("Deadlock in Operating Systems")
        self.play(FadeIn(title))
        
        intro_text = show_explanation("A deadlock occurs when processes are waiting for resources held by each other")
        self.wait(2)
        self.play(FadeOut(intro_text))

        # 2. Create Process and Resource objects
        p1 = Square(side_length=1.2, color=BLUE).shift(LEFT*3 + UP*1)
        p2 = Square(side_length=1.2, color=GREEN).shift(RIGHT*3 + UP*1)
        p1_label = Text("P1").move_to(p1.get_center())
        p2_label = Text("P2").move_to(p2.get_center())

        r1 = Circle(radius=0.6, color=YELLOW).shift(LEFT*3 + DOWN*1)
        r2 = Circle(radius=0.6, color=ORANGE).shift(RIGHT*3 + DOWN*1)
        r1_label = Text("R1").move_to(r1.get_center())
        r2_label = Text("R2").move_to(r2.get_center())

        self.play(FadeIn(p1, p2, r1, r2), Write(p1_label), Write(p2_label), Write(r1_label), Write(r2_label))
        
        legend_p = Text("Squares = Processes", color=BLUE, font_size=20).shift(DOWN*2.5 + LEFT*3)
        legend_r = Text("Circles = Resources", color=YELLOW, font_size=20).shift(DOWN*2.5 + RIGHT*3)
        self.play(Write(legend_p), Write(legend_r))
        self.wait(2)
        self.play(FadeOut(legend_p), FadeOut(legend_r))

        # 3. P1 acquires R1, P2 acquires R2
        step1_text = show_explanation("Step 1: Process P1 acquires Resource R1, Process P2 acquires Resource R2")
        
        arr_p1_r1 = Arrow(start=r1.get_top(), end=p1.get_bottom(), buff=0.1)
        arr_p2_r2 = Arrow(start=r2.get_top(), end=p2.get_bottom(), buff=0.1)
        self.play(GrowArrow(arr_p1_r1), GrowArrow(arr_p2_r2))
        self.play(Indicate(r1, scale_factor=1.1), Indicate(r2, scale_factor=1.1))
        self.wait(2)
        self.play(FadeOut(step1_text))

        # 4. P1 now requests R2
        step2_text = show_explanation("Step 2: Process P1 requests Resource R2 (but R2 is held by P2)")
        
        req1 = Arrow(start=p1.get_right() + DOWN*0.5, end=r2.get_left() + UP*0.2, buff=0.1, stroke_color=BLUE)
        self.play(GrowArrow(req1), run_time=1)
        self.play(req1.animate.set_color(RED), Flash(req1.get_end(), color=RED))
        self.play(Indicate(p1_label, scale_factor=1.2))
        self.wait(2)
        self.play(FadeOut(step2_text))

        # 5. P2 now requests R1
        step3_text = show_explanation("Step 3: Process P2 requests Resource R1 (but R1 is held by P1)")
        
        req2 = Arrow(start=p2.get_left() + DOWN*0.5, end=r1.get_right() + UP*0.2, buff=0.1, stroke_color=GREEN)
        self.play(GrowArrow(req2), run_time=1)
        self.play(req2.animate.set_color(RED), Flash(req2.get_end(), color=RED))
        self.play(Indicate(p2_label, scale_factor=1.2))
        self.wait(2)
        self.play(FadeOut(step3_text))

        # 6. Highlight circular wait
        step4_text = show_explanation("Step 4: Circular wait condition is formed - a defining characteristic of deadlock")
        
        cycle = VGroup(req1, arr_p1_r1, req2, arr_p2_r2)
        self.play(
            *[v.animate.set_stroke(width=6) for v in cycle],
            run_time=1
        )
        self.wait(2)
        self.play(FadeOut(step4_text))

        # 7. Show "Deadlock" text
        deadlock_text = Text("Deadlock Detected!", color=RED).scale(1.2)
        self.play(Write(deadlock_text))
        self.play(Shake(deadlock_text))  # Now using our custom Shake animation
        
        final_text = show_explanation(
            "Both P1 and P2 are permanently blocked waiting for resources\n" +
            "that will never be released - the system is in deadlock",
            position=DOWN*3.2
        )
        self.wait(3)