//TODO: declare your own package
package com.example.billingapp;

import org.onepf.oms.OpenIabHelper;
import org.onepf.oms.SkuManager;

import java.util.HashMap;
import java.util.Map;


public final class Config {

// TODO : SKUs for our products: the premium upgrade (non-consumable) and gas (consumable)

public static final String PROD_ONETIME  = "onetime";
public static final String PROD_MONTHLY_1= "month1";
public static final String PROD_MONTHLY_2= "month2";
public static final String PROD_MONTHLY_3= "month3";
public static final String PROD_ANNUAL_1 = "annual1";
public static final String PROD_ANNUAL_2 = "annual2";

/**
* TODO : your Google play public key.
*/
public static final String GOOGLE_PLAY_KEY= "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlTRIVTigerS/JKbUbCRBAvoApSujKEp+HRDtHGsTVwblBnbmO5Pkxipnjh0jwUrZn5UB7Myu5DlVrBiDontKnowWhatIAmDoingWithMyLifeX2liZi3NI/thisIsAFakePublicKey/F60unBF6vv/heHeh/hX5NdpMnVNCSRSQi/hahahahahahahahahahahahahahahaKXQjjkOqCy7LvQ+U7g5pSkWdWMccLQSIlq16hhJ6IStQbhaG0RiOjReGRTNbNzlCMQNGpVg5RqeCPMiOIpL4GKAODiD7vc3G72Op4udfwdemoPublicKey+QzwR7aY5OdHxvJIpnpQIDAQAC";

public static final Map<String, String> STORE_KEYS_MAP;

static {
STORE_KEYS_MAP = new HashMap<>();
STORE_KEYS_MAP.put("com.google.play", Config.GOOGLE_PLAY_KEY);

SkuManager.getInstance()
        .mapSku(PROD_ONETIME, "com.google.play", PROD_ONETIME)
        .mapSku(PROD_MONTHLY_1, "com.google.play", PROD_MONTHLY_1)
        .mapSku(PROD_MONTHLY_2, "com.google.play", PROD_MONTHLY_2)
        .mapSku(PROD_MONTHLY_3, "com.google.play", PROD_MONTHLY_3)
        .mapSku(PROD_ANNUAL_1, "com.google.play", PROD_ANNUAL_1)
        .mapSku(PROD_ANNUAL_2, "com.google.play", PROD_ANNUAL_2);
}

private Config() {
}
}
