"""授权管理单元测试."""

from pathlib import Path

from wx_mp_catcher.license.api import TrialStatusResult
from wx_mp_catcher.license.constants import TRIAL_IMAGE_LIMIT
from wx_mp_catcher.license.manager import LicenseManager, LicenseStatus
from wx_mp_catcher.license.store import LicenseState, LicenseStore


class _MockApi:
    def get_trial_status(self, device_id: str) -> TrialStatusResult:
        return TrialStatusResult(ok=False)

    def report_trial_usage(self, device_id: str, images_used: int) -> TrialStatusResult:
        return TrialStatusResult(ok=False)


def test_trial_limit_blocks_after_10_saves(tmp_path: Path):
    store = LicenseStore(tmp_path / "license_state.json")
    state = LicenseState(device_id="abc123device" * 2)
    store.save(state)
    manager = LicenseManager(store=store, api=_MockApi())

    for _ in range(TRIAL_IMAGE_LIMIT):
        assert manager.can_save_image()
        manager.record_image_saved()

    assert manager.get_status() == LicenseStatus.TRIAL_EXPIRED
    assert not manager.can_save_image()


def test_licensed_unlimited(tmp_path: Path):
    store = LicenseStore(tmp_path / "license_state.json")
    state = LicenseState(device_id="device1" * 4, license_token="token-xyz")
    store.save(state)
    manager = LicenseManager(store=store, api=_MockApi())
    assert manager.is_licensed()
    assert manager.can_save_image()
    assert manager.remaining_trial_images() == -1
