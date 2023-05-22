



def start_and_capture_files(self, name: str = "image{:03d}.jpg",
                                initial_delay=1, preview_mode="preview",
                                capture_mode="still", num_files=1, delay=1,
                                show_preview=True):
        """This function makes capturing multiple images more convenient.

        Should only be used in command line line applications (not from a Qt application, for example).
        If will configure the camera as requested and start it, switching between preview and still modes
        for capture. It supports the following parameters (all optional):

        name - name of the files to which to save the images. If more than one image is to be
            captured then it should feature a format directive that will be replaced by a counter.

        initial_delay - any time delay (in seconds) before the first image is captured. The camera
            will run in preview mode during this period. The default time is 1s.

        preview_mode - the camera mode to use for the preview phase (defaulting to the
            Picamera2 object's preview_configuration field).

        capture_mode - the camera mode to use to capture the still images (defaulting to the
            Picamera2 object's still_configuration field).

        num_files - number of files to capture (default 1).

        delay - the time delay for every capture after the first (default 1s).

        show_preview - whether to show a preview window (default: yes). The preview window only
            displays an image by default during the preview phase, so if captures are back-to-back
            with delay zero, then there may be no images shown. This parameter only has any
            effect if a preview is not already running. If it is, it would have to be stopped first
            (with the stop_preview method).
        """
        if self.started:
            self.stop()
        if delay:
            # Show a preview between captures, so we will switch mode and back for each capture.
            self.configure(preview_mode)
            self.start(show_preview=show_preview)
            for i in range(num_files):
                time.sleep(initial_delay if i == 0 else delay)
                self.switch_mode_and_capture_file(capture_mode, name.format(i))
        else:
            # No preview between captures, it's more efficient just to stay in capture mode.
            if initial_delay:
                self.configure(preview_mode)
                self.start(show_preview=show_preview)
                time.sleep(initial_delay)
                self.switch_mode(capture_mode)
            else:
                self.configure(capture_mode)
                self.start(show_preview=show_preview)
            for i in range(num_files):
                self.capture_file(name.format(i))
                if i == num_files - 1:
                    break
                time.sleep(delay)
        self.stop()