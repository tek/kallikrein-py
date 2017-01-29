from typing import Any, Dict

from golgi.config import ListConfigOption

metadata = dict(parents=['golgi'])


def reset_config() -> Dict[str, Any]:
    return {
        'run': dict(
            specs=ListConfigOption(),
        ),
    }
