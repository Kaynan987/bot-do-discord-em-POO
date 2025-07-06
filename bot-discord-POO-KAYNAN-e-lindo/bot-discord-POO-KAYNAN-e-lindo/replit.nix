{pkgs}: {
  deps = [
    pkgs.libopusenc
    pkgs.libopus
    pkgs.python311Packages.sounddevice
    pkgs.python311Packages.speechrecognition

  ];
}
