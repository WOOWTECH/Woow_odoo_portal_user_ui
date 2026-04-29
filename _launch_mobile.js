async page => {
  // Enable touch via CDP
  var client = await page.context().newCDPSession(page);
  await client.send('Emulation.setTouchEmulationEnabled', {
    enabled: true,
    maxTouchPoints: 5
  });
  await client.send('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 3,
    mobile: true
  });
  return 'Touch emulation enabled';
}
