# Document occupancy summary errors

`get_occupancy_summary` now returns an error dictionary when date parsing fails, but this behavior is not described in the docstring or README.

## Tasks
- [ ] Update the function docstring to mention the error cases and the shape of the returned dictionary.
- [ ] Add a short section in the README about the occupancy analysis tool and its expected input format.
