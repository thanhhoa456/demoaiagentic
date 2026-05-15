package com.qa.tests;

import com.qa.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * SampleTest
 * ─────────────────────────────────────────────────────────────
 * PLACEHOLDER - This file will be replaced by AI-generated
 * test classes from the AutomationTestcaseAgent.
 *
 * The agent will generate test classes following this pattern:
 *   - Extends BaseTest
 *   - Uses Page Object Model
 *   - TestNG @Test annotations with groups and description
 *   - Meaningful assertions
 * ─────────────────────────────────────────────────────────────
 */
public class SampleTest extends BaseTest {

    @Test(description = "Verify the framework is set up correctly")
    public void sampleFrameworkTest() {
        driver.get("https://www.google.com");
        String title = driver.getTitle();
        Assert.assertTrue(title.contains("Google"), "Page title should contain 'Google'");
    }
}
