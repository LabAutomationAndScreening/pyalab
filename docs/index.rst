.. pyalab documentation master file, created by
   sphinx-quickstart on Wed Dec 18 17:45:15 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pyalab documentation
====================

Pyalab allows you to use Python to generate programs for ViaLab to control an Integra Assist Plus liquid handling robot.

Once generated, the files can be simulated within ViaLab and further edited if needed.

The names of plates/pipettes/tips etc. should match the file names in the ``Integra Lib`` folder on your hard drive (typically found at ``C:\Program Files (x86)\INTEGRA Biosciences AG\VIALAB\Integra Lib``). These sometimes differ from the display names in Vialab itself.

At the moment, a limited subset of the full functionality of ViaLab is implemented, but more is being added each day.

Pyalab can be installed using ``pip install pyalab``.

Pyalab has been tested with Vialab 3.4.0.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   example
   steps
